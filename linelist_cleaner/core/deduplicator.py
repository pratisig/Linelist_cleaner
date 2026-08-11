"""
Exact and Fuzzy Patient Deduplication Engine.
"""

import datetime
from typing import Dict, List, Optional, Tuple, Any, Set
import pandas as pd
import numpy as np
from rapidfuzz import fuzz

from linelist_cleaner.schemas.models import DuplicateGroup


class Deduplicator:
    """Detects and resolves exact and probabilistic duplicate cases."""

    def __init__(
        self,
        fuzzy_threshold: float = 0.80,
        method: str = "both",  # "exact", "fuzzy", "both", "none"
        action: str = "flag"   # "flag", "keep_first", "keep_last", "keep_most_complete", "merge"
    ):
        self.fuzzy_threshold = fuzzy_threshold
        self.method = method
        self.action = action

    def find_duplicates(
        self,
        df: pd.DataFrame,
        tag_to_col: Dict[str, str]
    ) -> List[DuplicateGroup]:
        """
        Finds exact and fuzzy duplicate groups across the DataFrame.
        """
        if self.method == "none":
            return []

        duplicate_groups: List[DuplicateGroup] = []
        assigned_rows: Set[int] = set()
        group_id_counter = 1

        case_id_col = tag_to_col.get("case_id")
        name_col = tag_to_col.get("full_name") or tag_to_col.get("first_name")
        sex_col = tag_to_col.get("sex")
        age_col = tag_to_col.get("age")
        onset_col = tag_to_col.get("date_onset")

        n_rows = len(df)

        # 1. Exact Duplicate Rows or Exact Case ID Duplicates
        if self.method in ["exact", "both"]:
            # Exact rows
            exact_dup_indices = df[df.duplicated(keep=False)].index.tolist()
            if exact_dup_indices:
                groups_dict: Dict[Tuple, List[int]] = {}
                for idx in exact_dup_indices:
                    row_tuple = tuple(df.iloc[idx].astype(str).tolist())
                    groups_dict.setdefault(row_tuple, []).append(idx)

                for r_tuple, indices in groups_dict.items():
                    if len(indices) > 1:
                        best_idx = max(indices, key=lambda i: df.iloc[i].notna().sum())
                        cids = [str(df.iloc[i][case_id_col]) if case_id_col and pd.notna(df.iloc[i][case_id_col]) else f"Row {i+1}" for i in indices]
                        duplicate_groups.append(DuplicateGroup(
                            group_id=group_id_counter,
                            duplicate_type="exact",
                            match_score=1.0,
                            matching_keys={"all_columns": "Identical row content"},
                            row_indices=[i + 1 for i in indices],
                            case_ids=cids,
                            recommended_keep_idx=best_idx + 1
                        ))
                        group_id_counter += 1
                        assigned_rows.update(indices)

            # Duplicate Case ID (with different content)
            if case_id_col and case_id_col in df.columns:
                valid_ids = df[df[case_id_col].notna() & (df[case_id_col].astype(str).str.strip() != "")]
                dup_ids = valid_ids[valid_ids[case_id_col].duplicated(keep=False)]
                if not dup_ids.empty:
                    id_groups = dup_ids.groupby(case_id_col).groups
                    for cid_val, indices_idx in id_groups.items():
                        indices = list(indices_idx)
                        unassigned = [i for i in indices if i not in assigned_rows]
                        if len(unassigned) > 1:
                            best_idx = max(unassigned, key=lambda i: df.iloc[i].notna().sum())
                            duplicate_groups.append(DuplicateGroup(
                                group_id=group_id_counter,
                                duplicate_type="exact_id",
                                match_score=1.0,
                                matching_keys={"case_id": str(cid_val)},
                                row_indices=[i + 1 for i in unassigned],
                                case_ids=[str(cid_val)] * len(unassigned),
                                recommended_keep_idx=best_idx + 1
                            ))
                            group_id_counter += 1
                            assigned_rows.update(unassigned)

        # 2. Fuzzy Duplicates on Composite Demographics Keys
        if self.method in ["fuzzy", "both"] and name_col and name_col in df.columns:
            for i in range(n_rows):
                if i in assigned_rows:
                    continue

                name_i = str(df.iloc[i][name_col]).strip().lower() if pd.notna(df.iloc[i][name_col]) else ""
                if len(name_i) < 3:
                    continue

                cluster = [i]
                best_score = 0.0

                for j in range(i + 1, n_rows):
                    if j in assigned_rows:
                        continue

                    name_j = str(df.iloc[j][name_col]).strip().lower() if pd.notna(df.iloc[j][name_col]) else ""
                    if len(name_j) < 3:
                        continue

                    # Multi-metric fuzzy name similarity
                    sim_ratio = fuzz.ratio(name_i, name_j) / 100.0
                    sim_token_sort = fuzz.token_sort_ratio(name_i, name_j) / 100.0
                    sim_token_set = fuzz.token_set_ratio(name_i, name_j) / 100.0
                    sim_partial = fuzz.partial_ratio(name_i, name_j) / 100.0

                    sim_name = max(sim_ratio, sim_token_sort, sim_token_set, sim_partial)
                    if sim_name < self.fuzzy_threshold:
                        continue

                    # Demographics validation
                    # Sex check
                    if sex_col and pd.notna(df.iloc[i][sex_col]) and pd.notna(df.iloc[j][sex_col]):
                        if str(df.iloc[i][sex_col]).strip().lower() != str(df.iloc[j][sex_col]).strip().lower():
                            continue

                    # Age check (within 1.5 years)
                    if age_col and pd.notna(df.iloc[i][age_col]) and pd.notna(df.iloc[j][age_col]):
                        try:
                            age_i = float(df.iloc[i][age_col])
                            age_j = float(df.iloc[j][age_col])
                            if abs(age_i - age_j) > 1.5:
                                continue
                        except ValueError:
                            pass

                    # Date onset check (within 14 days if present)
                    if onset_col and pd.notna(df.iloc[i][onset_col]) and pd.notna(df.iloc[j][onset_col]):
                        try:
                            d_i = datetime.date.fromisoformat(str(df.iloc[i][onset_col])[:10])
                            d_j = datetime.date.fromisoformat(str(df.iloc[j][onset_col])[:10])
                            if abs((d_i - d_j).days) > 14:
                                continue
                        except Exception:
                            pass

                    cluster.append(j)
                    best_score = max(best_score, sim_name)

                if len(cluster) > 1:
                    best_idx = max(cluster, key=lambda idx_k: df.iloc[idx_k].notna().sum())
                    cids = [str(df.iloc[k][case_id_col]) if case_id_col and pd.notna(df.iloc[k][case_id_col]) else f"Row {k+1}" for k in cluster]
                    duplicate_groups.append(DuplicateGroup(
                        group_id=group_id_counter,
                        duplicate_type="fuzzy",
                        match_score=round(best_score, 2),
                        matching_keys={"name_similarity": round(best_score, 2)},
                        row_indices=[k + 1 for k in cluster],
                        case_ids=cids,
                        recommended_keep_idx=best_idx + 1
                    ))
                    group_id_counter += 1
                    assigned_rows.update(cluster)

        return duplicate_groups

    def resolve_duplicates(
        self,
        df: pd.DataFrame,
        groups: List[DuplicateGroup]
    ) -> Tuple[pd.DataFrame, int]:
        """
        Applies chosen resolution strategy to remove, flag, or merge duplicates.
        Returns: (resolved_df, count_of_records_removed)
        """
        if not groups or self.action == "flag":
            df_flagged = df.copy()
            dup_row_set = set()
            group_id_map = {}
            for g in groups:
                for r_1based in g.row_indices:
                    r_idx = r_1based - 1
                    dup_row_set.add(r_idx)
                    group_id_map[r_idx] = g.group_id

            df_flagged["is_duplicate"] = [i in dup_row_set for i in range(len(df))]
            df_flagged["duplicate_group_id"] = [group_id_map.get(i, None) for i in range(len(df))]
            return df_flagged, 0

        rows_to_drop: Set[int] = set()

        if self.action in ["keep_first", "keep_last", "keep_most_complete"]:
            for g in groups:
                indices_0based = [r - 1 for r in g.row_indices]
                if self.action == "keep_first":
                    keep_idx = indices_0based[0]
                elif self.action == "keep_last":
                    keep_idx = indices_0based[-1]
                else:
                    keep_idx = g.recommended_keep_idx - 1

                for idx in indices_0based:
                    if idx != keep_idx:
                        rows_to_drop.add(idx)

            df_cleaned = df.drop(index=list(rows_to_drop)).reset_index(drop=True)
            return df_cleaned, len(rows_to_drop)

        if self.action == "merge":
            df_merged = df.copy()
            for g in groups:
                indices_0based = [r - 1 for r in g.row_indices]
                primary_idx = g.recommended_keep_idx - 1
                for idx in indices_0based:
                    if idx != primary_idx:
                        for col in df_merged.columns:
                            if pd.isna(df_merged.at[primary_idx, col]) and pd.notna(df_merged.at[idx, col]):
                                df_merged.at[primary_idx, col] = df_merged.at[idx, col]
                        rows_to_drop.add(idx)

            df_cleaned = df_merged.drop(index=list(rows_to_drop)).reset_index(drop=True)
            return df_cleaned, len(rows_to_drop)

        return df, 0
