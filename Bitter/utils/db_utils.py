from .. import db_pool
from .misc_utils import DatabaseException
from contextlib import closing

def _get_db_connection():
    try:    return db_pool.get_connection()
    except: raise DatabaseException(503) # service unavailable

def _db_exec_commands(cursor, commands : list[str], fetch_all : list[bool]):
    results = []
    for idx, command in enumerate(commands):
        cursor.execute(command)
        results.append(cursor.fetchall() if fetch_all[idx] else cursor.fetchone())
    
    return results

def db_exec_multiple(*commands : list[str], commit = False, fetch_all : list[bool] = [False]) -> list[dict]:
    # each entry in the list fetch_all refers to the command with the same list index
    try:
        results = []
        with closing(_get_db_connection()) as conn:
            with closing(conn.cursor(dictionary=True)) as cursor:
                results = _db_exec_commands(cursor, commands, fetch_all)
            if commit:
                conn.commit()
        
        return results
    
    except Exception as e:
        raise DatabaseException(e)

def db_exec(command : str, commit = False, fetch_all = False) -> dict | None:
    db_results = db_exec_multiple(command, commit=commit, fetch_all=[fetch_all])
    if len(db_results):
        return db_results[0]
