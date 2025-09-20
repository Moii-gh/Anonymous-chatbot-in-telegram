# --- Структуры данных для хранения состояния бота ---

# {user_id: partner_id}
user_pairs = {}

# {user_id: {"gender": str, "interests": list, ...}}
user_profiles = {}

# {"male": [user_id_1, ...], "female": [...], "other": [...]}
waiting_queue = {"male": [], "female": [], "other": []}

# {user_id: [blocked_user_id_1, ...]}
blocked_pairs = {}

# {user_id: {"chats_count": int, "messages_sent": int}}
user_stats = {}

# {requester_id: partner_id}
exchange_requests = {}

# {user_id: {"partner_id": int, "move": str}}
active_games = {}

# {user_id: {original_message_id: partner_message_id}}
message_map = {}
