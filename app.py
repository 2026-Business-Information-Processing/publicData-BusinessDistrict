# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from supabase import create_client
except Exception:  # noqa: BLE001
    create_client = None


# =============================
# UI Labels (Korean via unicode escapes - ASCII safe in source)
# =============================
L = {
    "page_title": "\uc11c\uc6b8\uc2dc \uc0c1\uad8c\ubd84\uc11d \ub300\uc2dc\ubcf4\ub4dc MVP",
    "title": "\uc11c\uc6b8\uc2dc \uc0c1\uad8c\ubd84\uc11d\uc11c\ube44\uc2a4 2024 \ucc3d\uc5c5 \ucd94\ucc9c MVP",
    "caption": "\ud589\uc815\ub3d9\ubcc4 \uc0c1\uad8c \ud604\ud669 \uc2dc\uac01\ud654 + \uaddc\uce59 \uae30\ubc18 \ucc3d\uc5c5\uc720\ub9dd\uc9c0\uc5ed \ucd94\ucc9c",

    "filter_header": "\ud544\ud130",
    "filter_quarter": "\uae30\uc900_\ub144\ubd84\uae30_\ucf54\ub4dc",
    "filter_service": "\uc11c\ube44\uc2a4_\uc5c5\uc885_\ucf54\ub4dc_\uba85",
    "filter_min_stores": "\ucd5c\uc18c \uc810\ud3ec \uc218",
    "filter_top_n": "Top N",
    "filter_scatter_color": "\uc0b0\uc810\ub3c4 \uc0c9\uc0c1 \uae30\uc900",

    "all": "\uc804\uccb4",
    "warn_no_data": "\uc120\ud0dd\ud55c \uc870\uac74\uc5d0 \ud574\ub2f9\ud558\ub294 \ub370\uc774\ud130\uac00 \uc5c6\uc2b5\ub2c8\ub2e4. \ud544\ud130\ub97c \uc644\ud654\ud574 \uc8fc\uc138\uc694.",
    "warn_agg_empty": "\uc9d1\uacc4 \uacb0\uacfc\uac00 \ube44\uc5b4 \uc788\uc5b4 \uadf8\ub798\ud504\ub97c \ud45c\uc2dc\ud560 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.",
    "warn_scatter_empty": "\uc0b0\uc810\ub3c4\uc5d0 \ud45c\uc2dc\ud560 \ub370\uc774\ud130\uac00 \uc5c6\uc2b5\ub2c8\ub2e4.",

    "kpi_total_sales": "\ucd1d\ub9e4\ucd9c",
    "kpi_total_stores": "\ucd1d \uc810\ud3ec \uc218",
    "kpi_avg_sales_per_store": "\ud3c9\uade0 \uc810\ud3ec\ub2f9 \ub9e4\ucd9c",
    "kpi_avg_close_rate": "\ud3c9\uade0 \ud3d0\uc5c5\ub960",

    "section_charts": "\ud589\uc815\ub3d9\ubcc4 \uc0c1\uad8c \uc2dc\uac01\ud654",
    "section_reco": "\ucc3d\uc5c5\uc720\ub9dd\uc9c0\uc5ed \ucd94\ucc9c",
    "section_top5": "Top 5 \ud589\uc815\ub3d9 \uce74\ub4dc",
    "section_notes": "\uc720\uc758\uc0ac\ud56d",

    "chart_sales_title": "\ud589\uc815\ub3d9\ubcc4 \ucd1d\ub9e4\ucd9c Top {n}",
    "chart_sps_title": "\ud589\uc815\ub3d9\ubcc4 \uc810\ud3ec\ub2f9 \ub9e4\ucd9c Top {n}",
    "chart_scatter_title": "\uc720\ub3d9\uc778\uad6c\uc640 \ub9e4\ucd9c \uad00\uacc4 \uc0b0\uc810\ub3c4",
    "chart_reco_title": "\ucc3d\uc5c5\uc720\ub9dd\uc810\uc218 Top {n}",

    "axis_total_sales": "\ucd1d\ub9e4\ucd9c",
    "axis_sales_per_store": "\uc810\ud3ec\ub2f9\ub9e4\ucd9c",
    "axis_startup_score": "\ucc3d\uc5c5\uc720\ub9dd\uc810\uc218",
    "axis_pop": "\ucd1d_\uc720\ub3d9\uc778\uad6c_\uc218",
    "axis_amount": "\ub2f9\uc6d4_\ub9e4\ucd9c_\uae08\uc561",
    "axis_amount_won": "\ub9e4\ucd9c \uae08\uc561 (\uc6d0)",
    "axis_time_band": "\uc2dc\uac04\ub300",
    "axis_day_of_week": "\uc694\uc77c",

    "label_district": "\ud589\uc815\ub3d9",
    "label_total_sales": "\ucd1d\ub9e4\ucd9c",
    "label_store_count": "\uc810\ud3ec \uc218",
    "label_sales_per_store": "\uc810\ud3ec\ub2f9 \ub9e4\ucd9c",
    "label_close_rate": "\ud3d0\uc5c5\ub960",
    "label_pop": "\uc720\ub3d9\uc778\uad6c",
    "label_total_pop": "\ucd1d \uc720\ub3d9\uc778\uad6c",
    "label_startup_score": "\ucc3d\uc5c5\uc720\ub9dd\uc810\uc218",
    "label_score_sps": "\uc810\ud3ec\ub2f9\ub9e4\ucd9c\uc810\uc218",
    "label_score_pop": "\uc720\ub3d9\uc778\uad6c\uc810\uc218",
    "label_score_spop": "\uc720\ub3d9\uc778\uad6c\ub2f9\ub9e4\ucd9c\uc810\uc218",
    "label_score_close": "\ud3d0\uc5c5\ub960\uc548\uc815\uc131\uc810\uc218",
    "label_sales_per_pop": "\uc720\ub3d9\uc778\uad6c\ub2f9\ub9e4\ucd9c",

    "interp_sales_top": "\ud574\uc11d: \uc120\ud0dd \uc870\uac74\uc5d0\uc11c \ucd1d\ub9e4\ucd9c 1\uc704 \ud589\uc815\ub3d9\uc740 `{name}` \uc785\ub2c8\ub2e4.",
    "interp_sps_top": "\ud574\uc11d: \uc810\ud3ec\ub2f9 \ub9e4\ucd9c 1\uc704 \ud589\uc815\ub3d9\uc740 `{name}` \uc774\uba70, \uc810\ud3ec\ub2f9 \ub9e4\ucd9c\uc740 \ub9e4\ucd9c \ud6a8\uc728\uc744 \ubcf4\uc5ec\uc8fc\ub294 \uc9c0\ud45c\uc785\ub2c8\ub2e4.",
    "interp_reco_top": "\ud574\uc11d: \ucc3d\uc5c5\uc720\ub9dd\uc810\uc218 1\uc704 \ud589\uc815\ub3d9\uc740 `{name}` \uc774\uba70, \ub9e4\ucd9c \ud6a8\uc728 / \uc720\ub3d9\uc778\uad6c / \ub9e4\ucd9c \uc804\ud658\ub825 / \ud3d0\uc5c5\ub960 \uc548\uc815\uc131\uc744 \uc885\ud569\ud55c \uacb0\uacfc\uc785\ub2c8\ub2e4.",
    "quadrant_caption": (
        "- \uc720\ub3d9\uc778\uad6c \ub192\uc74c + \ub9e4\ucd9c \ub192\uc74c: \ub300\ud615 \ud65c\uc131 \uc0c1\uad8c  \n"
        "- \uc720\ub3d9\uc778\uad6c \ub192\uc74c + \ub9e4\ucd9c \ub0ae\uc74c: \uc720\ub3d9\uc740 \ub9ce\uc9c0\ub9cc \ub9e4\ucd9c \uc804\ud658 \uc57d\ud568  \n"
        "- \uc720\ub3d9\uc778\uad6c \ub0ae\uc74c + \ub9e4\ucd9c \ub192\uc74c: \ubaa9\uc801\ud615 \uc18c\ube44 \uc0c1\uad8c \uac00\ub2a5\uc131  \n"
        "- \uc720\ub3d9\uc778\uad6c \ub0ae\uc74c + \ub9e4\ucd9c \ub0ae\uc74c: \uc800\ud65c\uc131 \uc0c1\uad8c"
    ),

    "card_score": "\ucc3d\uc5c5\uc720\ub9dd\uc810\uc218",
    "card_avg_label": "\uc804\uccb4 \ud3c9\uade0",
    "card_strengths": "\uac15\uc810",
    "card_cautions": "\uc8fc\uc758\uc810",

    "section_detail": "\ucc3d\uc5c5 \ud6c4\ubcf4\uc9c0 \uc0c1\uc138 \ubd84\uc11d",
    "detail_select_label": "\uc0c1\uc138 \ubd84\uc11d\ud560 \ud589\uc815\ub3d9 \uc120\ud0dd",
    "detail_metrics_title": "\ud575\uc2ec \uc9c0\ud45c",
    "detail_compare_title": "\uc804\uccb4 \ud3c9\uade0 \ub300\ube44 \ube44\uad50",
    "detail_rank_title": "\uac19\uc740 \uc5c5\uc885 \ub0b4 \uc21c\uc704",
    "detail_strengths_title": "\uac15\uc810",
    "detail_cautions_title": "\uc8fc\uc758\uc810",
    "detail_summary_title": "\uc885\ud569 \ud310\ub2e8",
    "detail_compare_col_metric": "\uc9c0\ud45c",
    "detail_compare_col_value": "\uc120\ud0dd \ud589\uc815\ub3d9",
    "detail_compare_col_avg": "\uc804\uccb4 \ud3c9\uade0",
    "detail_compare_col_diff": "\ucc28\uc774",
    "detail_compare_col_interp": "\ud574\uc11d",
    "detail_rank_format": "{metric} \uc21c\uc704: {rank}\uc704 / {total}\uac1c \ud589\uc815\ub3d9",
    "detail_above_avg": "\ud3c9\uade0\ubcf4\ub2e4 \ub192\uc74c",
    "detail_below_avg": "\ud3c9\uade0\ubcf4\ub2e4 \ub0ae\uc74c",
    "detail_stable_close": "\ud3c9\uade0\ubcf4\ub2e4 \uc548\uc815\uc801",
    "detail_unstable_close": "\ud3c9\uade0\ubcf4\ub2e4 \ubd88\uc548\uc815",

    "section_time_day": "\uc2dc\uac04\ub300\ubcc4 / \uc694\uc77c\ubcc4 \ub9e4\ucd9c \ubd84\uc11d",
    "chart_time_title": "\uc2dc\uac04\ub300\ubcc4 \ub9e4\ucd9c \ube44\uc911",
    "chart_day_title": "\uc694\uc77c\ubcc4 \ub9e4\ucd9c \ube44\uc911",
    "time_no_cols": "\uc2dc\uac04\ub300 \ub9e4\ucd9c \uceec\ub7fc\uc774 \uc5c6\uc5b4 \uc2dc\uac04\ub300\ubcc4 \uadf8\ub798\ud504\ub294 \uc0dd\ub7b5\ud569\ub2c8\ub2e4.",
    "day_no_cols": "\uc694\uc77c\ubcc4 \ub9e4\ucd9c \uceec\ub7fc\uc774 \uc5c6\uc5b4 \uc694\uc77c\ubcc4 \uadf8\ub798\ud504\ub294 \uc0dd\ub7b5\ud569\ub2c8\ub2e4.",

    "interp_time_evening": "\uc800\ub141 \uc2dc\uac04\ub300 \uc18c\ube44\uac00 \uac15\ud55c \uc0c1\uad8c\uc73c\ub85c \ubcfc \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
    "interp_time_lunch": "\uc810\uc2ec \uc2dc\uac04\ub300 \uc18c\ube44 \ube44\uc911\uc774 \ub192\uc740 \uc0c1\uad8c\uc785\ub2c8\ub2e4.",
    "interp_time_morning": "\uc544\uce68 \uc2dc\uac04\ub300 \ub9e4\ucd9c\uc774 \uc8fc\ub3c4\uc801\uc778 \uc0c1\uad8c\uc73c\ub85c \ubcf4\uc785\ub2c8\ub2e4.",
    "interp_time_late": "\uc2ec\uc57c \uc2dc\uac04\ub300 \uc18c\ube44 \ube44\uc911\uc774 \ub192\uc740 \uc0c1\uad8c\uc785\ub2c8\ub2e4.",
    "interp_time_general": "\ud574\ub2f9 \uc2dc\uac04\ub300 \ub9e4\ucd9c \ube44\uc911\uc774 \uac00\uc7a5 \ub192\uc740 \uc0c1\uad8c\uc785\ub2c8\ub2e4.",
    "interp_day_weekend": "\uc8fc\ub9d0 \uc18c\ube44 \ube44\uc911\uc774 \ud070 \uc0c1\uad8c\uc73c\ub85c \ud574\uc11d\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
    "interp_day_weekday": "\ud3c9\uc77c \uc18c\ube44 \ube44\uc911\uc774 \ud070 \uc0c1\uad8c\uc73c\ub85c \ud574\uc11d\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.",

    "interp_time_template": "\uc120\ud0dd\ud55c \ud589\uc815\ub3d9\uc740 {peak} \ub9e4\ucd9c \ube44\uc911\uc774 \uac00\uc7a5 \ub192\uc544 {tail}",
    "interp_day_template": "\uc120\ud0dd\ud55c \ud589\uc815\ub3d9\uc740 {peak} \ub9e4\ucd9c \ube44\uc911\uc774 \uac00\uc7a5 \ub192\uc544 {tail}",

    "notes": [
        "- \ubcf8 \ub300\uc2dc\ubcf4\ub4dc\ub294 \uc11c\uc6b8\uc2dc \uc0c1\uad8c\ubd84\uc11d\uc11c\ube44\uc2a4\uc758 \ud589\uc815\ub3d9 \ub2e8\uc704 \ub370\uc774\ud130\ub97c \uae30\ubc18\uc73c\ub85c \ud569\ub2c8\ub2e4.",
        "- \uc784\ub300\ub8cc, \uad8c\ub9ac\uae08, \uc2e4\uc81c \uc601\uc5c5\uc774\uc775, \uac1c\ubcc4 \uc810\ud3ec \uc785\uc9c0 \uc870\uac74\uc740 \ud3ec\ud568\ud558\uc9c0 \uc54a\uc2b5\ub2c8\ub2e4.",
        "- \ucd94\ucc9c \uacb0\uacfc\ub294 \ucc3d\uc5c5 \ud6c4\ubcf4\uc9c0 \ud0d0\uc0c9\uc744 \uc704\ud55c \ucc38\uace0 \uc790\ub8cc\ub85c \ud65c\uc6a9\ud574\uc57c \ud569\ub2c8\ub2e4.",
    ],

    "spinner_load": "\ub370\uc774\ud130\ub97c \ubd88\ub7ec\uc624\ub294 \uc911\uc785\ub2c8\ub2e4...",
    "spinner_preprocess": "\ub370\uc774\ud130\ub97c \uc804\ucc98\ub9ac \ubc0f \uc810\uc218 \uacc4\uc0b0 \uc911\uc785\ub2c8\ub2e4...",
    "spinner_render": "\uadf8\ub798\ud504\ub97c \uc900\ube44\ud558\ub294 \uc911\uc785\ub2c8\ub2e4...",

    "reco_table_cols": {
        "dong_name": "\ud589\uc815\ub3d9_\ucf54\ub4dc_\uba85",
        "startup_score": "\ucc3d\uc5c5\uc720\ub9dd\uc810\uc218",
        "score_sales_per_store": "\uc810\ud3ec\ub2f9\ub9e4\ucd9c\uc810\uc218",
        "score_floating_pop": "\uc720\ub3d9\uc778\uad6c\uc810\uc218",
        "score_sales_per_floating_pop": "\uc720\ub3d9\uc778\uad6c\ub2f9\ub9e4\ucd9c\uc810\uc218",
        "score_close_stability": "\ud3d0\uc5c5\ub960\uc548\uc815\uc131\uc810\uc218",
        "total_sales": "\ucd1d\ub9e4\ucd9c",
        "avg_sales_per_store": "\uc810\ud3ec\ub2f9\ub9e4\ucd9c",
        "total_floating_pop": "\ucd1d_\uc720\ub3d9\uc778\uad6c_\uc218",
        "avg_sales_per_floating_pop": "\uc720\ub3d9\uc778\uad6c\ub2f9\ub9e4\ucd9c",
        "total_stores": "\uc810\ud3ec_\uc218",
        "avg_close_rate": "\ud3d0\uc5c5_\ub960",
        "reason": "\ucd94\ucc9c\uc0ac\uc720",
    },
}

REASONS = {
    "sps_high": "\uc810\ud3ec\ub2f9 \ub9e4\ucd9c\uc774 \ub192\uc544 \uae30\uc874 \uc810\ud3ec\uc758 \ub9e4\ucd9c \ud6a8\uc728\uc774 \uc88b\uc740 \uc9c0\uc5ed\uc785\ub2c8\ub2e4.",
    "pop_high": "\uc720\ub3d9\uc778\uad6c \uaddc\ubaa8\uac00 \ucee4 \uc7a0\uc7ac \uace0\uac1d \uc218\uc694\uac00 \ud48d\ubd80\ud55c \uc9c0\uc5ed\uc785\ub2c8\ub2e4.",
    "spop_high": "\uc720\ub3d9\uc778\uad6c \ub300\ube44 \ub9e4\ucd9c\uc774 \ub192\uc544 \uc2e4\uc81c \uc18c\ube44 \uc804\ud658\ub825\uc774 \uc88b\uc740 \uc0c1\uad8c\uc73c\ub85c \ubcfc \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
    "close_low": "\ud3d0\uc5c5\ub960\uc774 \ub0ae\uc544 \uc0c1\ub300\uc801\uc73c\ub85c \uc548\uc815\uc801\uc778 \uc0c1\uad8c\uc73c\ub85c \ud574\uc11d\ub429\ub2c8\ub2e4.",
    "close_high": "\ud3d0\uc5c5\ub960\uc774 \ub192\uc544 \ucc3d\uc5c5 \uc804 \uacbd\uc7c1 \uac15\ub3c4\uc640 \uc785\uc9c0 \uc870\uac74\uc744 \ucd94\uac00 \uac80\ud1a0\ud560 \ud544\uc694\uac00 \uc788\uc2b5\ub2c8\ub2e4.",
    "neutral_strength": "\ud575\uc2ec \uc9c0\ud45c\uac00 \ud3c9\uade0 \uc218\uc900\uc774\ubbc0\ub85c \uc5c5\uc885/\uc785\uc9c0\uc758 \uc815\uc131 \uac80\ud1a0\uac00 \ud544\uc694\ud569\ub2c8\ub2e4.",
    "neutral_caution": "\ud2b9\ubcc4\ud55c \uc704\ud5d8 \uc2e0\ud638\ub294 \ud06c\uc9c0 \uc54a\uc9c0\ub9cc \uc5c5\uc885 \ud2b9\uc131\ubcc4 \uc810\uac80\uc740 \ud544\uc694\ud569\ub2c8\ub2e4.",
}

DETAIL_REASONS = {
    "sps_above": "\uc810\ud3ec\ub2f9 \ub9e4\ucd9c\uc774 \ud3c9\uade0\ubcf4\ub2e4 \ub192\uc544 \ub9e4\ucd9c \ud6a8\uc728\uc774 \uc88b\uc740 \ud3b8\uc785\ub2c8\ub2e4.",
    "sps_below": "\uc810\ud3ec\ub2f9 \ub9e4\ucd9c\uc774 \ud3c9\uade0\ubcf4\ub2e4 \ub0ae\uc544 \ub9e4\ucd9c \ud6a8\uc728 \ucc28\uc6d0\uc758 \ub300\uc548\uc774 \ud544\uc694\ud569\ub2c8\ub2e4.",
    "pop_above": "\uc720\ub3d9\uc778\uad6c\uac00 \ud3c9\uade0\ubcf4\ub2e4 \ub9ce\uc544 \uc7a0\uc7ac \uc218\uc694\uac00 \ud48d\ubd80\ud55c \uc9c0\uc5ed\uc785\ub2c8\ub2e4.",
    "pop_below": "\uc720\ub3d9\uc778\uad6c\uac00 \ud3c9\uade0\ubcf4\ub2e4 \uc801\uc5b4 \uc218\uc694\ucc3d\ucd9c \uc804\ub7b5\uc774 \ud544\uc694\ud569\ub2c8\ub2e4.",
    "spop_above": "\uc720\ub3d9\uc778\uad6c \ub300\ube44 \ub9e4\ucd9c\uc774 \ud3c9\uade0\ubcf4\ub2e4 \ub192\uc544 \uc2e4\uc81c \uc18c\ube44 \uc804\ud658\ub825\uc774 \uc88b\uc2b5\ub2c8\ub2e4.",
    "spop_below": "\uc720\ub3d9\uc778\uad6c\ub294 \uc788\uc9c0\ub9cc \uc18c\ube44 \uc804\ud658\ub825\uc774 \ud3c9\uade0\ubcf4\ub2e4 \uc57d\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
    "close_below_avg": "\ud3d0\uc5c5\ub960\uc774 \ud3c9\uade0\ubcf4\ub2e4 \ub0ae\uc544 \uc0c1\ub300\uc801\uc73c\ub85c \uc548\uc815\uc801\uc778 \uc0c1\uad8c\uc73c\ub85c \ubcfc \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
    "close_above_avg": "\ud3d0\uc5c5\ub960\uc774 \ud3c9\uade0\ubcf4\ub2e4 \ub192\uc544 \ucc3d\uc5c5 \uc804 \ucd94\uac00 \uac80\ud1a0\uac00 \ud544\uc694\ud569\ub2c8\ub2e4.",
    "many_stores": "\uc810\ud3ec \uc218\uac00 \ub9ce\uc544 \uacbd\uc7c1 \uac15\ub3c4\uac00 \ub192\uc744 \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
    "summary_positive": "\uc120\ud0dd\ud55c \ud589\uc815\ub3d9\uc740 \ud575\uc2ec \uc9c0\ud45c\uac00 \uc804\uccb4 \ud3c9\uade0 \uc774\uc0c1\uc774\uc5b4 \ucc3d\uc5c5 \ud6c4\ubcf4\uc9c0\ub85c \uac80\ud1a0\ud560 \ub9cc\ud569\ub2c8\ub2e4. \ub2e4\ub9cc \uc810\ud3ec \uc218\uc640 \ud3d0\uc5c5\ub960\uc744 \ud568\uaed8 \ud655\uc778\ud574 \uc2e4\uc81c \uacbd\uc7c1 \uac15\ub3c4\ub97c \ucd94\uac00\ub85c \uc0b4\ud3b4\ubcfc \ud544\uc694\uac00 \uc788\uc2b5\ub2c8\ub2e4.",
    "summary_mixed": "\uc120\ud0dd\ud55c \ud589\uc815\ub3d9\uc740 \uc77c\ubd80 \uc9c0\ud45c\ub294 \uc804\uccb4 \ud3c9\uade0 \uc774\uc0c1\uc774\uc9c0\ub9cc \ub2e4\ub978 \uc9c0\ud45c\ub294 \ud3c9\uade0 \uc774\ud558\uc785\ub2c8\ub2e4. \uc5c5\uc885 \ud2b9\uc131\uacfc \uc785\uc9c0 \uc870\uac74\uc744 \ud568\uaed8 \uac80\ud1a0\ud55c \ub4a4 \uacb0\uc815\ud558\ub294 \uac83\uc774 \uc88b\uc2b5\ub2c8\ub2e4.",
    "summary_negative": "\uc120\ud0dd\ud55c \ud589\uc815\ub3d9\uc740 \ud575\uc2ec \uc9c0\ud45c \ub300\ubd80\ubd84\uc774 \uc804\uccb4 \ud3c9\uade0\ubcf4\ub2e4 \ub0ae\uc544 \uc2e0\uc911\ud55c \uac80\ud1a0\uac00 \ud544\uc694\ud569\ub2c8\ub2e4.",
}

# Original Korean column names from raw CSV (for time-band / day-of-week)
TIME_BAND_COLS = [
    ("\uc2dc\uac04\ub300_00~06_\ub9e4\ucd9c_\uae08\uc561", "00~06\uc2dc"),
    ("\uc2dc\uac04\ub300_06~11_\ub9e4\ucd9c_\uae08\uc561", "06~11\uc2dc"),
    ("\uc2dc\uac04\ub300_11~14_\ub9e4\ucd9c_\uae08\uc561", "11~14\uc2dc"),
    ("\uc2dc\uac04\ub300_14~17_\ub9e4\ucd9c_\uae08\uc561", "14~17\uc2dc"),
    ("\uc2dc\uac04\ub300_17~21_\ub9e4\ucd9c_\uae08\uc561", "17~21\uc2dc"),
    ("\uc2dc\uac04\ub300_21~24_\ub9e4\ucd9c_\uae08\uc561", "21~24\uc2dc"),
]
DAY_OF_WEEK_COLS = [
    ("\uc6d4\uc694\uc77c_\ub9e4\ucd9c_\uae08\uc561", "\uc6d4"),
    ("\ud654\uc694\uc77c_\ub9e4\ucd9c_\uae08\uc561", "\ud654"),
    ("\uc218\uc694\uc77c_\ub9e4\ucd9c_\uae08\uc561", "\uc218"),
    ("\ubaa9\uc694\uc77c_\ub9e4\ucd9c_\uae08\uc561", "\ubaa9"),
    ("\uae08\uc694\uc77c_\ub9e4\ucd9c_\uae08\uc561", "\uae08"),
    ("\ud1a0\uc694\uc77c_\ub9e4\ucd9c_\uae08\uc561", "\ud1a0"),
    ("\uc77c\uc694\uc77c_\ub9e4\ucd9c_\uae08\uc561", "\uc77c"),
]

st.set_page_config(page_title=L["page_title"], layout="wide")


# =============================
# Constants
# =============================
SUPABASE_TABLES = {
    "sales_2024": "sales_2024",
    "stores_2024": "stores_2024",
    "population_2024": "population_2024",
}


# =============================
# Formatting helpers
# =============================
def format_currency_krw(value: float) -> str:
    if pd.isna(value):
        return "-"
    value = float(value)
    abs_v = abs(value)
    sign = "-" if value < 0 else ""
    if abs_v >= 100_000_000:
        return f"{sign}{abs_v / 100_000_000:.1f}\uc5b5 \uc6d0"
    if abs_v >= 10_000:
        return f"{sign}{abs_v / 10_000:.1f}\ub9cc \uc6d0"
    return f"{sign}{int(round(abs_v)):,}\uc6d0"


def format_number(value: float) -> str:
    if pd.isna(value):
        return "-"
    return f"{int(round(value)):,}"


def format_percent(value: float, digits: int = 1) -> str:
    if pd.isna(value):
        return "-"
    return f"{value:.{digits}f}%"


def format_score(value: float) -> str:
    if pd.isna(value):
        return "-"
    return f"{value:.1f}\uc810"


# =============================
# Data loading (Supabase only)
# =============================
def get_supabase_credentials() -> tuple[str, str]:
    supa_url = None
    supa_key = None

    if "supabase" in st.secrets:
        supa_url = st.secrets["supabase"].get("url")
        supa_key = st.secrets["supabase"].get("key")
    if not supa_url or not supa_key:
        supa_url = st.secrets.get("SUPABASE_URL")
        supa_key = st.secrets.get("SUPABASE_KEY")
    if (not supa_url or not supa_key) and "connections" in st.secrets:
        connections = st.secrets["connections"]
        if "supabase" in connections:
            conn = connections["supabase"]
            supa_url = supa_url or conn.get("SUPABASE_URL") or conn.get("url")
            supa_key = supa_key or conn.get("SUPABASE_KEY") or conn.get("key")

    if not supa_url or not supa_key:
        top_keys = ", ".join(list(st.secrets.keys()))
        raise KeyError(
            "Supabase URL/KEY not found. "
            "Supported: [supabase] url/key, SUPABASE_URL/SUPABASE_KEY, "
            "[connections.supabase] SUPABASE_URL/SUPABASE_KEY. "
            f"(Top-level keys: {top_keys})"
        )
    return supa_url, supa_key


def fetch_all_rows(client, table_name: str, page_size: int = 1000) -> list[dict]:
    # For large tables, range pagination may need additional tuning.
    all_rows: list[dict] = []
    start = 0
    while True:
        end = start + page_size - 1
        response = client.table(table_name).select("*").range(start, end).execute()
        rows = response.data or []
        all_rows.extend(rows)
        if len(rows) < page_size:
            break
        start += page_size
    return all_rows


@st.cache_data(show_spinner=False, ttl=300)
def load_data_from_supabase() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if create_client is None:
        raise ImportError("`supabase` package is missing. Install dependencies and retry.")
    supa_url, supa_key = get_supabase_credentials()
    client = create_client(supa_url, supa_key)
    sales_rows = fetch_all_rows(client, SUPABASE_TABLES["sales_2024"])
    stores_rows = fetch_all_rows(client, SUPABASE_TABLES["stores_2024"])
    pop_rows = fetch_all_rows(client, SUPABASE_TABLES["population_2024"])
    sales = pd.DataFrame(sales_rows)
    stores = pd.DataFrame(stores_rows)
    population = pd.DataFrame(pop_rows)
    if sales.empty or stores.empty or population.empty:
        raise ValueError("Supabase table empty or no read permission.")
    return sales, stores, population


# =============================
# Preprocess / scoring
# =============================
def to_numeric_safe(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace("%", "", regex=False)
    )
    cleaned = cleaned.replace({"": np.nan, "-": np.nan, "nan": np.nan, "None": np.nan})
    return pd.to_numeric(cleaned, errors="coerce")


def safe_divide(numer: pd.Series, denom: pd.Series) -> pd.Series:
    return numer / denom.replace(0, np.nan)


def minmax_0_100(series: pd.Series) -> pd.Series:
    s = series.astype(float)
    min_v = s.min(skipna=True)
    max_v = s.max(skipna=True)
    if pd.isna(min_v) or pd.isna(max_v):
        return pd.Series(0.0, index=series.index)
    if np.isclose(min_v, max_v):
        return pd.Series(50.0, index=series.index)
    return ((s - min_v) / (max_v - min_v) * 100).clip(0, 100)


def validate_columns_shape(df: pd.DataFrame, at_least: int, name: str) -> None:
    if df.shape[1] < at_least:
        raise ValueError(f"{name}: expected at least {at_least} columns, got {df.shape[1]}")


def standardize_columns_by_position(
    sales_raw: pd.DataFrame,
    stores_raw: pd.DataFrame,
    pop_raw: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    validate_columns_shape(sales_raw, 7, "sales_2024")
    validate_columns_shape(stores_raw, 10, "stores_2024")
    validate_columns_shape(pop_raw, 4, "population_2024")

    sales = sales_raw.rename(
        columns={
            sales_raw.columns[0]: "quarter_code",
            sales_raw.columns[1]: "dong_code",
            sales_raw.columns[2]: "dong_name",
            sales_raw.columns[3]: "service_code",
            sales_raw.columns[4]: "service_name",
            sales_raw.columns[5]: "monthly_sales_amount",
            sales_raw.columns[6]: "monthly_sales_count",
        }
    ).copy()

    stores_map = {
        stores_raw.columns[0]: "quarter_code",
        stores_raw.columns[1]: "dong_code",
        stores_raw.columns[2]: "dong_name",
        stores_raw.columns[3]: "service_code",
        stores_raw.columns[4]: "service_name",
        stores_raw.columns[5]: "store_count",
        stores_raw.columns[9]: "close_rate",
    }
    if stores_raw.shape[1] > 11:
        stores_map[stores_raw.columns[11]] = "franchise_store_count"
    stores = stores_raw.rename(columns=stores_map).copy()

    population = pop_raw.rename(
        columns={
            pop_raw.columns[0]: "quarter_code",
            pop_raw.columns[1]: "dong_code",
            pop_raw.columns[2]: "dong_name",
            pop_raw.columns[3]: "floating_population",
        }
    ).copy()

    return sales, stores, population


def build_master_dataframe(
    sales_raw: pd.DataFrame,
    stores_raw: pd.DataFrame,
    pop_raw: pd.DataFrame,
) -> pd.DataFrame:
    sales, stores, population = standardize_columns_by_position(sales_raw, stores_raw, pop_raw)

    keys_sales_stores = [
        "quarter_code",
        "dong_code",
        "dong_name",
        "service_code",
        "service_name",
    ]
    keys_pop = ["quarter_code", "dong_code", "dong_name"]

    merged = pd.merge(sales, stores, on=keys_sales_stores, how="inner")
    merged = pd.merge(merged, population, on=keys_pop, how="left")

    base_numeric_cols = [
        "monthly_sales_amount",
        "monthly_sales_count",
        "store_count",
        "close_rate",
        "floating_population",
        "franchise_store_count",
    ]
    time_band_cols_in_df = [c for c, _ in TIME_BAND_COLS if c in merged.columns]
    day_cols_in_df = [c for c, _ in DAY_OF_WEEK_COLS if c in merged.columns]

    for col in base_numeric_cols + time_band_cols_in_df + day_cols_in_df:
        if col in merged.columns:
            merged[col] = to_numeric_safe(merged[col])

    merged["sales_per_store"] = safe_divide(merged["monthly_sales_amount"], merged["store_count"])
    merged["sales_count_per_store"] = safe_divide(merged["monthly_sales_count"], merged["store_count"])
    merged["sales_per_floating_pop"] = safe_divide(
        merged["monthly_sales_amount"], merged["floating_population"]
    )
    merged["sales_count_per_floating_pop"] = safe_divide(
        merged["monthly_sales_count"], merged["floating_population"]
    )
    merged["avg_ticket"] = safe_divide(merged["monthly_sales_amount"], merged["monthly_sales_count"])
    if "franchise_store_count" in merged.columns:
        merged["franchise_ratio"] = safe_divide(merged["franchise_store_count"], merged["store_count"])
    else:
        merged["franchise_ratio"] = np.nan

    merged = merged.replace([np.inf, -np.inf], np.nan)

    merged["score_sales_per_store"] = minmax_0_100(merged["sales_per_store"])
    merged["score_floating_pop"] = minmax_0_100(merged["floating_population"])
    merged["score_sales_per_floating_pop"] = minmax_0_100(merged["sales_per_floating_pop"])
    merged["score_close_stability"] = (100 - minmax_0_100(merged["close_rate"])).clip(0, 100)
    merged["startup_score"] = (
        0.35 * merged["score_sales_per_store"]
        + 0.25 * merged["score_floating_pop"]
        + 0.25 * merged["score_sales_per_floating_pop"]
        + 0.15 * merged["score_close_stability"]
    )
    return merged


def split_strengths_and_cautions(row: pd.Series) -> tuple[list[str], list[str]]:
    strengths: list[str] = []
    cautions: list[str] = []

    if row["score_sales_per_store"] >= 70:
        strengths.append(REASONS["sps_high"])
    if row["score_floating_pop"] >= 70:
        strengths.append(REASONS["pop_high"])
    if row["score_sales_per_floating_pop"] >= 70:
        strengths.append(REASONS["spop_high"])
    if row["score_close_stability"] >= 70:
        strengths.append(REASONS["close_low"])
    if row["score_close_stability"] < 40:
        cautions.append(REASONS["close_high"])
    if not strengths:
        strengths.append(REASONS["neutral_strength"])
    if not cautions:
        cautions.append(REASONS["neutral_caution"])
    return strengths, cautions


def prepare_display_columns(agg: pd.DataFrame) -> pd.DataFrame:
    disp = agg.copy()
    disp["disp_total_sales"] = disp["total_sales"].apply(format_currency_krw)
    disp["disp_sales_per_store"] = disp["avg_sales_per_store"].apply(format_currency_krw)
    disp["disp_sales_per_pop"] = disp["avg_sales_per_floating_pop"].apply(format_currency_krw)
    disp["disp_pop"] = disp["total_floating_pop"].apply(format_number)
    disp["disp_stores"] = disp["total_stores"].apply(format_number)
    disp["disp_close_rate"] = disp["avg_close_rate"].apply(lambda x: format_percent(x, 2))
    disp["disp_startup_score"] = disp["startup_score"].apply(format_score)
    disp["disp_score_sps"] = disp["score_sales_per_store"].apply(format_score)
    disp["disp_score_pop"] = disp["score_floating_pop"].apply(format_score)
    disp["disp_score_spop"] = disp["score_sales_per_floating_pop"].apply(format_score)
    disp["disp_score_close"] = disp["score_close_stability"].apply(format_score)
    return disp


# =============================
# Detail analysis helpers
# =============================
def compute_rank(values: pd.Series, target_value: float, higher_is_better: bool = True) -> tuple[int, int]:
    clean = values.dropna()
    total = len(clean)
    if total == 0 or pd.isna(target_value):
        return 0, total
    if higher_is_better:
        rank = int((clean > target_value).sum()) + 1
    else:
        rank = int((clean < target_value).sum()) + 1
    return rank, total


def detail_interpret_value(target: float, avg: float, lower_is_better: bool = False) -> str:
    if pd.isna(target) or pd.isna(avg):
        return "-"
    if lower_is_better:
        if target < avg:
            return L["detail_stable_close"]
        if target > avg:
            return L["detail_unstable_close"]
        return L["detail_above_avg"] if target >= avg else L["detail_below_avg"]
    if target > avg:
        return L["detail_above_avg"]
    if target < avg:
        return L["detail_below_avg"]
    return L["detail_above_avg"]


def build_detail_strengths_cautions(
    target_row: pd.Series, overall_avg: dict, total_stores_avg: float
) -> tuple[list[str], list[str]]:
    strengths: list[str] = []
    cautions: list[str] = []

    if target_row["avg_sales_per_store"] >= overall_avg["avg_sales_per_store"]:
        strengths.append(DETAIL_REASONS["sps_above"])
    else:
        cautions.append(DETAIL_REASONS["sps_below"])

    if target_row["total_floating_pop"] >= overall_avg["total_floating_pop"]:
        strengths.append(DETAIL_REASONS["pop_above"])
    else:
        cautions.append(DETAIL_REASONS["pop_below"])

    if target_row["avg_sales_per_floating_pop"] >= overall_avg["avg_sales_per_floating_pop"]:
        strengths.append(DETAIL_REASONS["spop_above"])
    else:
        cautions.append(DETAIL_REASONS["spop_below"])

    if not pd.isna(target_row["avg_close_rate"]):
        if target_row["avg_close_rate"] < overall_avg["avg_close_rate"]:
            strengths.append(DETAIL_REASONS["close_below_avg"])
        else:
            cautions.append(DETAIL_REASONS["close_above_avg"])

    if not pd.isna(target_row["total_stores"]) and not pd.isna(total_stores_avg):
        if target_row["total_stores"] > total_stores_avg * 1.2:
            cautions.append(DETAIL_REASONS["many_stores"])

    return strengths, cautions


def build_detail_summary(strengths: list[str], cautions: list[str]) -> str:
    s_count = len(strengths)
    c_count = len(cautions)
    if s_count >= 3 and c_count <= 1:
        return DETAIL_REASONS["summary_positive"]
    if s_count <= 1 and c_count >= 3:
        return DETAIL_REASONS["summary_negative"]
    return DETAIL_REASONS["summary_mixed"]


# =============================
# UI render helpers
# =============================
def render_top_charts(
    agg_disp: pd.DataFrame,
    top_n: int,
    scatter_color_metric: str,
) -> None:
    # 1) Sales Top N
    top_sales = agg_disp.sort_values("total_sales", ascending=False).head(top_n)
    top_sales_sorted = top_sales.sort_values("total_sales")
    fig_sales = px.bar(
        top_sales_sorted,
        x="total_sales",
        y="dong_name",
        orientation="h",
        title=L["chart_sales_title"].format(n=top_n),
    )
    fig_sales.update_traces(
        customdata=np.stack(
            [
                top_sales_sorted["dong_name"],
                top_sales_sorted["disp_total_sales"],
                top_sales_sorted["disp_stores"],
                top_sales_sorted["disp_sales_per_store"],
                top_sales_sorted["disp_close_rate"],
            ],
            axis=-1,
        ),
        hovertemplate=(
            f"<b>{L['label_district']}</b>: %{{customdata[0]}}<br>"
            f"<b>{L['label_total_sales']}</b>: %{{customdata[1]}}<br>"
            f"<b>{L['label_store_count']}</b>: %{{customdata[2]}}<br>"
            f"<b>{L['label_sales_per_store']}</b>: %{{customdata[3]}}<br>"
            f"<b>{L['label_close_rate']}</b>: %{{customdata[4]}}<extra></extra>"
        ),
    )
    fig_sales.update_layout(yaxis_title="", xaxis_title=L["axis_total_sales"])
    st.plotly_chart(fig_sales, width="stretch")
    st.caption(L["interp_sales_top"].format(name=top_sales.iloc[0]["dong_name"]))

    # 2) Sales per store Top N
    top_sps = agg_disp.sort_values("avg_sales_per_store", ascending=False).head(top_n)
    top_sps_sorted = top_sps.sort_values("avg_sales_per_store")
    fig_sps = px.bar(
        top_sps_sorted,
        x="avg_sales_per_store",
        y="dong_name",
        orientation="h",
        title=L["chart_sps_title"].format(n=top_n),
    )
    fig_sps.update_traces(
        customdata=np.stack(
            [
                top_sps_sorted["dong_name"],
                top_sps_sorted["disp_sales_per_store"],
                top_sps_sorted["disp_total_sales"],
                top_sps_sorted["disp_stores"],
                top_sps_sorted["disp_pop"],
                top_sps_sorted["disp_close_rate"],
            ],
            axis=-1,
        ),
        hovertemplate=(
            f"<b>{L['label_district']}</b>: %{{customdata[0]}}<br>"
            f"<b>{L['label_sales_per_store']}</b>: %{{customdata[1]}}<br>"
            f"<b>{L['label_total_sales']}</b>: %{{customdata[2]}}<br>"
            f"<b>{L['label_store_count']}</b>: %{{customdata[3]}}<br>"
            f"<b>{L['label_pop']}</b>: %{{customdata[4]}}<br>"
            f"<b>{L['label_close_rate']}</b>: %{{customdata[5]}}<extra></extra>"
        ),
    )
    fig_sps.update_layout(yaxis_title="", xaxis_title=L["axis_sales_per_store"])
    st.plotly_chart(fig_sps, width="stretch")
    st.caption(L["interp_sps_top"].format(name=top_sps.iloc[0]["dong_name"]))

    # 3) Scatter
    scatter = agg_disp.dropna(subset=["total_floating_pop", "total_sales", "total_stores"]).copy()
    if scatter.empty:
        st.warning(L["warn_scatter_empty"])
        return

    color_col = scatter_color_metric if scatter_color_metric in scatter.columns else "startup_score"
    fig_scatter = px.scatter(
        scatter,
        x="total_floating_pop",
        y="total_sales",
        size="total_stores",
        color=color_col,
        title=L["chart_scatter_title"],
    )
    fig_scatter.update_traces(
        customdata=np.stack(
            [
                scatter["dong_name"],
                scatter["disp_pop"],
                scatter["disp_total_sales"],
                scatter["disp_stores"],
                scatter["disp_sales_per_store"],
                scatter["disp_startup_score"],
            ],
            axis=-1,
        ),
        hovertemplate=(
            f"<b>{L['label_district']}</b>: %{{customdata[0]}}<br>"
            f"<b>{L['label_total_pop']}</b>: %{{customdata[1]}}<br>"
            f"<b>{L['label_total_sales']}</b>: %{{customdata[2]}}<br>"
            f"<b>{L['label_store_count']}</b>: %{{customdata[3]}}<br>"
            f"<b>{L['label_sales_per_store']}</b>: %{{customdata[4]}}<br>"
            f"<b>{L['label_startup_score']}</b>: %{{customdata[5]}}<extra></extra>"
        ),
    )
    fig_scatter.add_vline(
        x=scatter["total_floating_pop"].mean(skipna=True),
        line_dash="dot",
        line_color="gray",
    )
    fig_scatter.add_hline(
        y=scatter["total_sales"].mean(skipna=True),
        line_dash="dot",
        line_color="gray",
    )
    fig_scatter.update_layout(xaxis_title=L["axis_pop"], yaxis_title=L["axis_amount"])
    st.plotly_chart(fig_scatter, width="stretch")
    st.markdown(L["quadrant_caption"])


def render_recommendation_section(
    agg_disp: pd.DataFrame, top_n: int, overall_avg: dict
) -> pd.DataFrame:
    st.subheader(L["section_reco"])
    reco = agg_disp.sort_values("startup_score", ascending=False).head(top_n).copy()
    reco["strengths"] = reco.apply(lambda r: split_strengths_and_cautions(r)[0], axis=1)
    reco["cautions"] = reco.apply(lambda r: split_strengths_and_cautions(r)[1], axis=1)
    reco["reason"] = reco["strengths"].apply(lambda xs: " ".join(xs))

    cols_map = L["reco_table_cols"]
    reco_table = reco.rename(columns=cols_map)
    st.dataframe(
        reco_table[
            [
                cols_map["dong_name"],
                cols_map["startup_score"],
                cols_map["score_sales_per_store"],
                cols_map["score_floating_pop"],
                cols_map["score_sales_per_floating_pop"],
                cols_map["score_close_stability"],
                cols_map["total_sales"],
                cols_map["avg_sales_per_store"],
                cols_map["total_floating_pop"],
                cols_map["avg_sales_per_floating_pop"],
                cols_map["total_stores"],
                cols_map["avg_close_rate"],
                cols_map["reason"],
            ]
        ],
        width="stretch",
    )

    reco_sorted = reco.sort_values("startup_score")
    fig_reco = px.bar(
        reco_sorted,
        x="startup_score",
        y="dong_name",
        orientation="h",
        title=L["chart_reco_title"].format(n=top_n),
        color="startup_score",
        color_continuous_scale="Blues",
    )
    fig_reco.update_traces(
        customdata=np.stack(
            [
                reco_sorted["dong_name"],
                reco_sorted["disp_startup_score"],
                reco_sorted["disp_score_sps"],
                reco_sorted["disp_score_pop"],
                reco_sorted["disp_score_spop"],
                reco_sorted["disp_score_close"],
            ],
            axis=-1,
        ),
        hovertemplate=(
            f"<b>{L['label_district']}</b>: %{{customdata[0]}}<br>"
            f"<b>{L['label_startup_score']}</b>: %{{customdata[1]}}<br>"
            f"<b>{L['label_score_sps']}</b>: %{{customdata[2]}}<br>"
            f"<b>{L['label_score_pop']}</b>: %{{customdata[3]}}<br>"
            f"<b>{L['label_score_spop']}</b>: %{{customdata[4]}}<br>"
            f"<b>{L['label_score_close']}</b>: %{{customdata[5]}}<extra></extra>"
        ),
    )
    fig_reco.update_layout(yaxis_title="", xaxis_title=L["axis_startup_score"])
    st.plotly_chart(fig_reco, width="stretch")
    st.caption(L["interp_reco_top"].format(name=reco.iloc[0]["dong_name"]))

    # Top 5 cards
    st.markdown(f"### {L['section_top5']}")
    top5 = reco.head(5)
    cols = st.columns(5)
    for idx, row in top5.reset_index(drop=True).iterrows():
        strengths, cautions = split_strengths_and_cautions(row)
        with cols[idx]:
            st.markdown(f"#### {idx + 1}. {row['dong_name']}")
            st.markdown(f"- {L['card_score']}: **{format_score(row['startup_score'])}**")
            st.markdown(
                f"- {L['label_sales_per_store']}: {format_currency_krw(row['avg_sales_per_store'])} / "
                f"{L['card_avg_label']} {format_currency_krw(overall_avg['avg_sales_per_store'])}"
            )
            st.markdown(
                f"- {L['label_total_pop']}: {format_number(row['total_floating_pop'])} / "
                f"{L['card_avg_label']} {format_number(overall_avg['total_floating_pop'])}"
            )
            st.markdown(
                f"- {L['label_sales_per_pop']}: "
                f"{format_currency_krw(row['avg_sales_per_floating_pop'])} / "
                f"{L['card_avg_label']} {format_currency_krw(overall_avg['avg_sales_per_floating_pop'])}"
            )
            st.markdown(
                f"- {L['label_close_rate']}: {format_percent(row['avg_close_rate'], 2)} / "
                f"{L['card_avg_label']} {format_percent(overall_avg['avg_close_rate'], 2)}"
            )
            st.markdown(f"**{L['card_strengths']}**")
            for s in strengths:
                st.caption(f"- {s}")
            st.markdown(f"**{L['card_cautions']}**")
            for c in cautions:
                st.caption(f"- {c}")
    return reco


# =============================
# Detail section
# =============================
def render_candidate_detail(
    agg: pd.DataFrame,
    reco_df: pd.DataFrame,
    overall_avg: dict,
) -> str:
    """Returns selected dong_name so caller can reuse for the time/day section."""
    st.subheader(L["section_detail"])

    dong_options = agg["dong_name"].dropna().astype(str).tolist()
    if not dong_options:
        st.warning(L["warn_agg_empty"])
        return ""

    default_dong = reco_df.iloc[0]["dong_name"] if not reco_df.empty else dong_options[0]
    default_idx = dong_options.index(default_dong) if default_dong in dong_options else 0
    selected_dong = st.selectbox(L["detail_select_label"], dong_options, index=default_idx)

    target_row = agg[agg["dong_name"] == selected_dong].iloc[0]

    # 1-1) Core metrics
    st.markdown(f"#### {L['detail_metrics_title']}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(L["label_total_sales"], format_currency_krw(target_row["total_sales"]))
    c2.metric(L["label_sales_per_store"], format_currency_krw(target_row["avg_sales_per_store"]))
    c3.metric(L["label_total_pop"], format_number(target_row["total_floating_pop"]))
    c4.metric(L["label_sales_per_pop"], format_currency_krw(target_row["avg_sales_per_floating_pop"]))

    c5, c6, c7, _ = st.columns(4)
    c5.metric(L["label_store_count"], format_number(target_row["total_stores"]))
    c6.metric(L["label_close_rate"], format_percent(target_row["avg_close_rate"], 2))
    c7.metric(L["label_startup_score"], format_score(target_row["startup_score"]))

    # 1-2) Comparison table
    st.markdown(f"#### {L['detail_compare_title']}")
    compare_rows = [
        {
            L["detail_compare_col_metric"]: L["label_sales_per_store"],
            L["detail_compare_col_value"]: format_currency_krw(target_row["avg_sales_per_store"]),
            L["detail_compare_col_avg"]: format_currency_krw(overall_avg["avg_sales_per_store"]),
            L["detail_compare_col_diff"]: format_currency_krw(
                target_row["avg_sales_per_store"] - overall_avg["avg_sales_per_store"]
            ),
            L["detail_compare_col_interp"]: detail_interpret_value(
                target_row["avg_sales_per_store"], overall_avg["avg_sales_per_store"]
            ),
        },
        {
            L["detail_compare_col_metric"]: L["label_total_pop"],
            L["detail_compare_col_value"]: format_number(target_row["total_floating_pop"]),
            L["detail_compare_col_avg"]: format_number(overall_avg["total_floating_pop"]),
            L["detail_compare_col_diff"]: format_number(
                target_row["total_floating_pop"] - overall_avg["total_floating_pop"]
            ),
            L["detail_compare_col_interp"]: detail_interpret_value(
                target_row["total_floating_pop"], overall_avg["total_floating_pop"]
            ),
        },
        {
            L["detail_compare_col_metric"]: L["label_sales_per_pop"],
            L["detail_compare_col_value"]: format_currency_krw(
                target_row["avg_sales_per_floating_pop"]
            ),
            L["detail_compare_col_avg"]: format_currency_krw(
                overall_avg["avg_sales_per_floating_pop"]
            ),
            L["detail_compare_col_diff"]: format_currency_krw(
                target_row["avg_sales_per_floating_pop"]
                - overall_avg["avg_sales_per_floating_pop"]
            ),
            L["detail_compare_col_interp"]: detail_interpret_value(
                target_row["avg_sales_per_floating_pop"],
                overall_avg["avg_sales_per_floating_pop"],
            ),
        },
        {
            L["detail_compare_col_metric"]: L["label_close_rate"],
            L["detail_compare_col_value"]: format_percent(target_row["avg_close_rate"], 2),
            L["detail_compare_col_avg"]: format_percent(overall_avg["avg_close_rate"], 2),
            L["detail_compare_col_diff"]: format_percent(
                target_row["avg_close_rate"] - overall_avg["avg_close_rate"], 2
            ),
            L["detail_compare_col_interp"]: detail_interpret_value(
                target_row["avg_close_rate"], overall_avg["avg_close_rate"], lower_is_better=True
            ),
        },
        {
            L["detail_compare_col_metric"]: L["label_startup_score"],
            L["detail_compare_col_value"]: format_score(target_row["startup_score"]),
            L["detail_compare_col_avg"]: format_score(overall_avg.get("startup_score", np.nan)),
            L["detail_compare_col_diff"]: format_score(
                target_row["startup_score"] - overall_avg.get("startup_score", np.nan)
            ),
            L["detail_compare_col_interp"]: detail_interpret_value(
                target_row["startup_score"], overall_avg.get("startup_score", np.nan)
            ),
        },
    ]
    st.dataframe(pd.DataFrame(compare_rows), width="stretch")

    # 1-3) Rankings
    st.markdown(f"#### {L['detail_rank_title']}")
    rank_metrics = [
        (L["label_total_sales"], agg["total_sales"], target_row["total_sales"], True),
        (L["label_sales_per_store"], agg["avg_sales_per_store"], target_row["avg_sales_per_store"], True),
        (L["label_total_pop"], agg["total_floating_pop"], target_row["total_floating_pop"], True),
        (
            L["label_sales_per_pop"],
            agg["avg_sales_per_floating_pop"],
            target_row["avg_sales_per_floating_pop"],
            True,
        ),
        (
            L["label_score_close"],
            agg["score_close_stability"],
            target_row["score_close_stability"],
            True,
        ),
        (L["label_startup_score"], agg["startup_score"], target_row["startup_score"], True),
    ]
    rank_cols = st.columns(3)
    for idx, (metric_name, series, target_val, higher_is_better) in enumerate(rank_metrics):
        rank, total = compute_rank(series, target_val, higher_is_better)
        rank_text = (
            L["detail_rank_format"].format(metric=metric_name, rank=rank, total=total)
            if rank > 0
            else f"{metric_name}: -"
        )
        rank_cols[idx % 3].markdown(f"- {rank_text}")

    # 1-4) Strengths / cautions
    total_stores_avg = agg["total_stores"].mean(skipna=True)
    strengths, cautions = build_detail_strengths_cautions(target_row, overall_avg, total_stores_avg)
    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown(f"#### {L['detail_strengths_title']}")
        for s in strengths:
            st.markdown(f"- {s}")
    with sc2:
        st.markdown(f"#### {L['detail_cautions_title']}")
        for c in cautions:
            st.markdown(f"- {c}")

    # 1-5) Summary
    st.markdown(f"#### {L['detail_summary_title']}")
    st.info(build_detail_summary(strengths, cautions))

    return selected_dong


# =============================
# Time-of-day / day-of-week section
# =============================
def _peak_interpretation_for_time(label: str) -> str:
    if label.startswith("17") or label.startswith("21"):
        return L["interp_time_evening"]
    if label.startswith("11"):
        return L["interp_time_lunch"]
    if label.startswith("06"):
        return L["interp_time_morning"]
    if label.startswith("00"):
        return L["interp_time_late"]
    return L["interp_time_general"]


def _peak_interpretation_for_day(label: str) -> str:
    weekend_chars = {"\ud1a0", "\uc77c"}
    return L["interp_day_weekend"] if label in weekend_chars else L["interp_day_weekday"]


def render_time_and_day_section(filtered_df: pd.DataFrame, selected_dong: str) -> None:
    st.subheader(L["section_time_day"])

    if not selected_dong:
        return

    dong_df = filtered_df[filtered_df["dong_name"].astype(str) == selected_dong]
    if dong_df.empty:
        st.warning(L["warn_no_data"])
        return

    time_pairs = [(col, label) for col, label in TIME_BAND_COLS if col in dong_df.columns]
    day_pairs = [(col, label) for col, label in DAY_OF_WEEK_COLS if col in dong_df.columns]

    chart_cols = st.columns(2)

    # Time chart
    with chart_cols[0]:
        if not time_pairs:
            st.info(L["time_no_cols"])
        else:
            time_values = [dong_df[col].sum(skipna=True) for col, _ in time_pairs]
            time_labels = [label for _, label in time_pairs]
            time_df = pd.DataFrame({"time_band": time_labels, "sales": time_values})
            time_df["disp_sales"] = time_df["sales"].apply(format_currency_krw)
            fig_t = px.bar(
                time_df,
                x="time_band",
                y="sales",
                title=L["chart_time_title"],
                color="sales",
                color_continuous_scale="Blues",
            )
            fig_t.update_traces(
                customdata=np.stack(
                    [time_df["time_band"], time_df["disp_sales"]], axis=-1
                ),
                hovertemplate=(
                    f"<b>{L['axis_time_band']}</b>: %{{customdata[0]}}<br>"
                    f"<b>{L['label_total_sales']}</b>: %{{customdata[1]}}<extra></extra>"
                ),
            )
            fig_t.update_layout(xaxis_title=L["axis_time_band"], yaxis_title=L["axis_amount_won"])
            st.plotly_chart(fig_t, width="stretch")

            if time_df["sales"].sum() > 0:
                peak_row = time_df.loc[time_df["sales"].idxmax()]
                tail = _peak_interpretation_for_time(peak_row["time_band"])
                st.caption(
                    L["interp_time_template"].format(peak=peak_row["time_band"], tail=tail)
                )

    # Day chart
    with chart_cols[1]:
        if not day_pairs:
            st.info(L["day_no_cols"])
        else:
            day_values = [dong_df[col].sum(skipna=True) for col, _ in day_pairs]
            day_labels = [label for _, label in day_pairs]
            day_df = pd.DataFrame({"day": day_labels, "sales": day_values})
            day_df["disp_sales"] = day_df["sales"].apply(format_currency_krw)
            fig_d = px.bar(
                day_df,
                x="day",
                y="sales",
                title=L["chart_day_title"],
                color="sales",
                color_continuous_scale="Oranges",
            )
            fig_d.update_traces(
                customdata=np.stack(
                    [day_df["day"], day_df["disp_sales"]], axis=-1
                ),
                hovertemplate=(
                    f"<b>{L['axis_day_of_week']}</b>: %{{customdata[0]}}<br>"
                    f"<b>{L['label_total_sales']}</b>: %{{customdata[1]}}<extra></extra>"
                ),
            )
            fig_d.update_layout(xaxis_title=L["axis_day_of_week"], yaxis_title=L["axis_amount_won"])
            st.plotly_chart(fig_d, width="stretch")

            if day_df["sales"].sum() > 0:
                peak_row = day_df.loc[day_df["sales"].idxmax()]
                tail = _peak_interpretation_for_day(peak_row["day"])
                st.caption(L["interp_day_template"].format(peak=peak_row["day"], tail=tail))


# =============================
# Main dashboard
# =============================
def render_dashboard(df: pd.DataFrame) -> None:
    st.title(L["title"])
    st.caption(L["caption"])

    st.sidebar.header(L["filter_header"])
    quarter_options = [L["all"]] + sorted(df["quarter_code"].dropna().astype(str).unique().tolist())
    service_options = [L["all"]] + sorted(df["service_name"].dropna().astype(str).unique().tolist())

    selected_quarter = st.sidebar.selectbox(L["filter_quarter"], quarter_options, index=0)
    selected_service = st.sidebar.selectbox(L["filter_service"], service_options, index=0)
    min_store = st.sidebar.number_input(L["filter_min_stores"], min_value=0, value=3, step=1)
    top_n = st.sidebar.slider(L["filter_top_n"], min_value=5, max_value=30, value=10, step=1)
    scatter_color_metric = st.sidebar.selectbox(
        L["filter_scatter_color"], ["close_rate", "startup_score"], index=0
    )

    filtered = df.copy()
    if selected_quarter != L["all"]:
        filtered = filtered[filtered["quarter_code"].astype(str) == selected_quarter]
    if selected_service != L["all"]:
        filtered = filtered[filtered["service_name"].astype(str) == selected_service]
    filtered = filtered[filtered["store_count"].fillna(0) >= min_store]

    if filtered.empty:
        st.warning(L["warn_no_data"])
        return

    total_sales = filtered["monthly_sales_amount"].sum(skipna=True)
    total_stores = filtered["store_count"].sum(skipna=True)
    avg_sales_per_store = filtered["sales_per_store"].mean(skipna=True)
    avg_close_rate = filtered["close_rate"].mean(skipna=True)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(L["kpi_total_sales"], format_currency_krw(total_sales))
    k2.metric(L["kpi_total_stores"], format_number(total_stores))
    k3.metric(L["kpi_avg_sales_per_store"], format_currency_krw(avg_sales_per_store))
    k4.metric(L["kpi_avg_close_rate"], format_percent(avg_close_rate, 2))

    with st.spinner(L["spinner_render"]):
        agg = (
            filtered.groupby("dong_name", as_index=False)
            .agg(
                total_sales=("monthly_sales_amount", "sum"),
                total_stores=("store_count", "sum"),
                total_floating_pop=("floating_population", "sum"),
                avg_close_rate=("close_rate", "mean"),
                avg_sales_per_store=("sales_per_store", "mean"),
                avg_sales_per_floating_pop=("sales_per_floating_pop", "mean"),
                score_sales_per_store=("score_sales_per_store", "mean"),
                score_floating_pop=("score_floating_pop", "mean"),
                score_sales_per_floating_pop=("score_sales_per_floating_pop", "mean"),
                score_close_stability=("score_close_stability", "mean"),
                startup_score=("startup_score", "mean"),
            )
            .replace([np.inf, -np.inf], np.nan)
        )

        if agg.empty:
            st.warning(L["warn_agg_empty"])
            return

        agg_disp = prepare_display_columns(agg)
        overall_avg = {
            "avg_sales_per_store": agg["avg_sales_per_store"].mean(skipna=True),
            "total_floating_pop": agg["total_floating_pop"].mean(skipna=True),
            "avg_sales_per_floating_pop": agg["avg_sales_per_floating_pop"].mean(skipna=True),
            "avg_close_rate": agg["avg_close_rate"].mean(skipna=True),
            "startup_score": agg["startup_score"].mean(skipna=True),
        }

    st.subheader(L["section_charts"])
    render_top_charts(agg_disp, top_n, scatter_color_metric)

    reco_df = render_recommendation_section(agg_disp, top_n, overall_avg)

    selected_dong = render_candidate_detail(agg, reco_df, overall_avg)

    if selected_dong:
        render_time_and_day_section(filtered, selected_dong)

    st.markdown("---")
    st.markdown(f"### {L['section_notes']}")
    for note in L["notes"]:
        st.markdown(note)


def main() -> None:
    try:
        with st.spinner(L["spinner_load"]):
            sales_raw, stores_raw, pop_raw = load_data_from_supabase()
    except Exception as exc:  # noqa: BLE001
        st.error(
            "Supabase \ub370\uc774\ud130 \ub85c\ub529 \uc911 \uc624\ub958\uac00 \ubc1c\uc0dd\ud588\uc2b5\ub2c8\ub2e4.\n"
            f"\uc6d0\uc778: {exc}"
        )
        return

    try:
        with st.spinner(L["spinner_preprocess"]):
            master = build_master_dataframe(sales_raw, stores_raw, pop_raw)
    except Exception as exc:  # noqa: BLE001
        st.error(
            "\ub370\uc774\ud130 \uacb0\ud569/\uc804\ucc98\ub9ac/\uc810\uc218 \uacc4\uc0b0 \uc911 \uc624\ub958\uac00 \ubc1c\uc0dd\ud588\uc2b5\ub2c8\ub2e4.\n"
            f"\uc6d0\uc778: {exc}"
        )
        return

    if master.empty:
        st.warning(
            "\uacb0\ud569\ub41c \ub370\uc774\ud130\uac00 \ube44\uc5b4 \uc788\uc5b4 \ub300\uc2dc\ubcf4\ub4dc\ub97c \ud45c\uc2dc\ud560 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4."
        )
        return

    render_dashboard(master)


if __name__ == "__main__":
    main()
