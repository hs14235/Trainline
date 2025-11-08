# booking/__init__.py
try:
    import pymysql  # only needed when using MySQL locally
    pymysql.install_as_MySQLdb()
except Exception:
    pass
