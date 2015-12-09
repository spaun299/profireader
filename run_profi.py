from profapp import create_app
import argparse

if __name__ == '__main__':
    app_profi = create_app(front='n')

    app_profi.run(host='0.0.0.0', port=8080, debug=True)  #app.run(debug=True)

    #app.run()
