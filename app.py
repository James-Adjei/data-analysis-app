from flask import Flask, render_template,request,flash

app=Flask(__name__)
app.secret_key="ideine15445"

@app.route("/",methods=["GET"])
def index()->str:
    flash("What's Your Name?")
    return render_template("index.html")



@app.route("/greet",methods=["POST","GET"])
def greet()->str:
    minput= str( request.form["name_input"])
    flash("Hi "+minput+", Good to see you!")

    return render_template("index.html")
# if __name__=="__app__":
#     app.run(debug=True)



