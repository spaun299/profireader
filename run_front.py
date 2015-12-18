from profapp import create_app
import argparse

app_front = create_app(front='y')
if __name__ == '__main__':
    app_front.run(host='0.0.0.0', port=8888, debug=True)  #app.run(debug=True)
    #app.run()
