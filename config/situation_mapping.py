# config/situation_mapping.py
SITUATION_MAPPING = {
    "batter": {
        "vs_RHP": {"code": "vr", "description": "vs Right-Handed Pitcher"},
        "vs_LHP": {"code": "vl", "description": "vs Left-Handed Pitcher"},
    },
    "pitcher": {
        "vs_RHB": {"code": "vr", "description": "vs Right-Handed Batter"},
        "vs_LHB": {"code": "vl", "description": "vs Left-Handed Batter"},
    },
    "menOnBase": {
        "Empty": {"code": "r0", "description": "No Runner On Base"},
        "RISP": {"code": "risp", "description": "Runner In Scoring Position"},
        "Men_On": {"code": "ron", "description": "Runner On Base"},
        "Loaded": {"code": "r123", "description": "Bases Loaded"},
    },
}
