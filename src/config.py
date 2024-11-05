import os

class Config:
    # Use the hostname "db" - defined in compose.yaml - as database hostname
    SQLALCHEMY_DATABASE_URI = 'postgresql://inventorydbuser:password@db:5432/inventorydb'
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'postgresql://user:password@localhost/dbname')

    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable to save memory

    UPLOAD_FOLDER = 'input/'

    # SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    SECRET_KEY = 'thisisasecretkey'

# Will need to adjust this file to accommodate testing...
# if 'pytest' in sys.modules:
#     # Use the dynamic connection URL provided by the test container during tests
#     app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_TEST_URI', 'postgresql://inventorydbuser:password@localhost:5432/inventorydb')
# else:
#     # Use the hostname "db" - defined in compose.yaml - as database hostname
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://inventorydbuser:password@db:5432/inventorydb'