from werkzeug.security import generate_password_hash
from db_additions import register_admin
from data.db_session import global_init

global_init('1')
register_admin('admin', generate_password_hash('nimda'), 'admin@admin.ru', 'admin')