def data_quality_report(df):
    stats = df.describe(include="all").to_dict()

    # Sanitize NaNs for JSON compatibility
    def sanitize(obj):
        if isinstance(obj, float) and (obj != obj or obj == float('inf') or obj == float('-inf')):
            return None
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        return obj
    
    return {
        "missing": df.isnull().sum().to_dict(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "duplicates": int(df.duplicated().sum()),
        "stats": sanitize(stats)
    }
