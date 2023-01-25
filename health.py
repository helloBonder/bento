from flask import Flask, make_response

app = Flask(__name__)

@app.route("/health")
def health():
    
    return make_response('Health Check OK', 200)


if __name__ == "__main__":
    app.run(debug=True)