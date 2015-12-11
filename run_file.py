from profapp import create_app
import argparse

if __name__ == '__main__':
    app_file = create_app(front='f')
    #app.run(host='127.40.71.198', port=8080)  #app.run(debug=True)

    app_file.run(host='0.0.0.0', port=9001, debug=True)  #app.run(debug=True)
