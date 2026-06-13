def check_fraud_signals(bidders_data: list) -> list:
    """
    bidders_data: list of {"bidder_id": int, "filename": str, "verdicts": list}
    Returns list of fraud flags: cross-bidder matches on key fields.
    """
    flags = []

    # Extract GST numbers per bidder
    gst_map = {}
    for bidder in bidders_data:
        for v in bidder["verdicts"]:
            if v["criterion_name"] == "GST Registration" and v["extracted_value"]:
                gst = str(v["extracted_value"]).strip().replace('"', '')
                if gst and gst != "None":
                    gst_map.setdefault(gst, []).append(bidder["filename"])

    for gst, filenames in gst_map.items():
        if len(filenames) > 1:
            flags.append({
                "type": "SHARED_GST",
                "detail": f"GST number {gst} appears in multiple bidder submissions: {', '.join(filenames)}",
                "bidders": filenames
            })

    # Extract turnover values for price-proximity check
    turnover_map = {}
    for bidder in bidders_data:
        for v in bidder["verdicts"]:
            if v["criterion_name"] == "Annual Turnover" and v["extracted_value"]:
                try:
                    val = float(str(v["extracted_value"]).strip('"'))
                    turnover_map[bidder["filename"]] = val
                except (ValueError, TypeError):
                    pass

    filenames = list(turnover_map.keys())
    for i in range(len(filenames)):
        for j in range(i + 1, len(filenames)):
            a, b = filenames[i], filenames[j]
            val_a, val_b = turnover_map[a], turnover_map[b]
            if val_a > 0 and abs(val_a - val_b) / val_a < 0.005:
                flags.append({
                    "type": "PRICE_PROXIMITY",
                    "detail": f"{a} and {b} report nearly identical turnover values ({val_a} vs {val_b}), within 0.5%",
                    "bidders": [a, b]
                })

    return flags