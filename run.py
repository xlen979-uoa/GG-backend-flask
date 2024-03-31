from app import app
import warnings
warnings.filterwarnings('ignore')

if __name__ == '__main__':
    if not app.config['DEBUG']:
        app.run()
        #app.run(debug=app.config['DEBUG'],
        #        host=app.config['HOST'],
        #        port=app.config['PORT'],
        #        ssl_context=(
        #            app.config['SSH_NAME_PATH'],
        #            app.config['SSH_KEY_PATH']))
    else:
        app.run(debug=app.config['DEBUG'],
                host=app.config['HOST'],
                port=app.config['PORT'])
