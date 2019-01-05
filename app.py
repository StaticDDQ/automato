from flask import Flask , render_template , g , redirect , jsonify
from flask_sqlalchemy import SQLAlchemy 
import MySQLdb
import pika 
import json 

app = Flask(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)
from model import contacts , scrape_form , scrape_task , job_form , job_task


def connect_queue():
    if not hasattr(g , 'rabbitmq'):
        g.rabbitmq = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    return g.rabbitmq

def get_scraper_queue():
    if not hasattr(g ,'task_queue'):
        conn = connect_queue()
        channel = conn.channel()
        channel.queue_declare(queue = 'scraper_queue' , durable=True)
        channel.queue_bind(exchange='amq.direct' , queue = 'scraper_queue')
        g.task_queue = channel 
    return g.task_queue 

def destroy_scraper_queue():
    if hasattr(g , 'task_queue'):
        g.task_queue.queue_delete(queue = "scraper_queue")
    else:
        print("Scraper Queue not availabel")

def get_mssg_queue():
    if not hasattr(g ,'mssg_queue'):
        conn = connect_queue()
        channel = conn.channel()
        channel.queue_declare(queue = 'mssg_queue' , durable=True)
        channel.queue_bind(exchange='amq.direct' , queue = 'mssg_queue')
        g.mssg_queue = channel 
    return g.mssg_queue 


@app.teardown_appcontext
def close_queue(error):
    if hasattr(g , 'rabbitmq'):
        g.rabbitmq.close()


@app.route('/' , methods = ['GET' , 'POST'])
def home():
    
    con_len = db.session.query(contacts).count()
    city_len = db.session.query(contacts.city).distinct(contacts.city).count()

    src_len = db.session.query(scrape_task).count()
    src_fin = db.session.query(scrape_task).filter_by(status = str(2)).count()
    src_unfin = db.session.query(scrape_task).filter_by(status = str(0)).count()
    src_run = db.session.query(scrape_task).filter_by(status = str(1)).count()

    job_len = db.session.query(job_task).count()
    job_fin = db.session.query(job_task).filter_by(status = str(2)).count()
    job_unfin = db.session.query(job_task).filter_by(status = str(3)).count()
    print(job_unfin)
    job_run = db.session.query(job_task).filter_by(status = str(1)).count()

    return render_template('dash.html' , con_len = con_len , city_len = city_len , src_len = src_len , src_fin = src_fin ,\
        src_unfin = src_unfin , src_run = src_run , job_len = job_len , job_fin = job_fin ,\
        job_unfin = job_unfin , job_run = job_run) , 200

@app.route('/scheduler' ,methods = ['GET' , 'POST'])
def scheduler():
    return render_template('scheduler.html') , 200

@app.route('/jobs' ,methods = ['GET' , 'POST'])
def jobs():
    form = job_form()
    form.city.choices = [ (r.city , r.city ) for r in db.session.query(scrape_task) ]

    job_list = db.session.query(job_task).all()
    if form.validate_on_submit():
        city = form.city.data 
        provider = "Whatsapp"
        # Check if the city and keyword already exsists ?
        check_one = db.session.query(job_task).filter_by(city = city , provider = provider).first()
        if check_one is None:
            new_job = job_task(city = city  , provider = provider , status = str(0) , meta = str(''))
            db.session.add(new_job)
            db.session.commit()
            mssg = "Scraper added to list."
            print(mssg)
            return redirect('/jobs')
        else:
            mssg = "Scraper already exsists. You can rerun the scraper from the list below , or run a new scraper with different parameters." 
            print(mssg)
            return redirect('/jobs')
    else:
        print(form.errors)
    return render_template('jobs.html' , form= form , mssg = None , job_list = job_list) , 200

@app.route('/contacts' ,methods = ['GET' , 'POST'])
def contacts_call():
    # contacts_list = db.session.query(contacts).all()
    return render_template('contacts.html' ) , 200

@app.route('/task_pause' , methods = ['POST'])
def task_pause(task_id):
    # Destroys the queue and the message 
    pass

@app.route('/scraper', methods = ['GET' , 'POST'])
def scraper():
    form = scrape_form()
    scraper_list = db.session.query(scrape_task).all()
    print(scraper_list)
    if form.validate_on_submit():
        city = form.city.data 
        keyword = form.keyword.data  
        provider = "Justdial"
        # Check if the city and keyword already exsists ?
        check_one = db.session.query(scrape_task).filter_by(city = city , keyword = keyword , provider = provider).first()
        if check_one is None:
            new_scraper =scrape_task(city = city , keyword = keyword , provider = provider , status = str(0) , meta = str(1))
            db.session.add(new_scraper)
            db.session.commit()
            mssg = "Scraper added to list."
            print(mssg)
            return redirect('/scraper')
        else:
            mssg = "Scraper already exsists. You can rerun the scraper from the list below , or run a new scraper with different parameters." 
            print(mssg)
            return redirect('/scraper')
    return render_template('scraper.html' , form= form , mssg = None ,scraper_list = scraper_list) , 200


@app.route('/push_scraper_to_queue/<task_id>' , methods = ['POST' , 'GET'])
def push_scraper_to_queue(task_id):

    # Pushes the task to scraper run queue 
    # Runs only one task a time 
    try:
        task = db.session.query(scrape_task).filter_by(id = task_id).first()
        search_data = {'city' : task.city , 'keyword' : task.keyword , 'page' : task.meta , 'task_id' : task_id}
        q = get_scraper_queue()
        q.basic_publish(
            exchange='amq.direct',
            routing_key='scraper_queue',
            body=json.dumps(search_data),
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )
        task.status = 1
        db.session.commit()
        return redirect('/scraper')
    except Exception as e:
        mssg = "We ran into an error : " + str(e)
        print(mssg)
        return redirect('/scraper')

@app.route('/push_job_to_queue/<task_id>' , methods = ['POST' , 'GET'])
def push_job_to_queue(task_id):

    # Pushes the task to scraper run queue 
    # Runs only one task a time 
    try:
        task = db.session.query(job_task).filter_by(id = task_id).first()
        job_data = {'city' : task.city ,'meta' : task.meta , 'task_id' : task_id}
        m = get_mssg_queue()
        print(m)
        print("Ok")
        m.basic_publish(
            exchange='amq.direct',
            routing_key='mssg_queue',
            body=json.dumps(job_data),
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )
        task.status = 1
        db.session.commit()
        return redirect('/jobs')
    except Exception as e:
        mssg = "We ran into an error : " + str(e)
        print(mssg)
        return redirect('/jobs')

@app.route('/job_results/<job_id>' , methods= ['POST' , 'GET'])
def job_results(job_id):
    try:
        job_city = db.session.query(job_task).filter_by(id = str(job_id)).first().city
        print(job_city)
        success_all = db.session.query(contacts).filter_by(city = job_city).filter((contacts.wp_cnt == 1)).all()
        invalid_all = db.session.query(contacts).filter_by(city = job_city).filter((contacts.wp_cnt == -2)).all()
        jdnum_all = db.session.query(contacts).filter_by(city = job_city).filter((contacts.wp_cnt == 0)).all()
        unable_all = db.session.query(contacts).filter_by(city = job_city).filter((contacts.wp_cnt == -1)).all()

        # success_sent = [x if x.wp_cnt is 1 else None for x in contacts]
        # invalid_sent = [x if x.wp_cnt is -2 else None for x in contacts]
        # jd_number = [x if x.wp_cnt is 0 else None for x in contacts]
        # unable_Sent = [x if x.wp_cnt is -1 else None for x in contacts]
        
        return jsonify({'success_all' : len(success_all) , 'invalid_all' : len(invalid_all)})
    except Exception as e:
        pass
        return "Naah" + str(e)

@app.route('/src_results/<job_id>' , methods= ['POST' , 'GET'])
def src_results(job_id):
    try:
        src_city = db.session.query(scrape_task).filter_by(id = str(job_id)).first().city
        print(src_city)
        success_all = db.session.query(contacts).filter_by(city = src_city).all()
        # success_sent = [x if x.wp_cnt is 1 else None for x in contacts]
        # invalid_sent = [x if x.wp_cnt is -2 else None for x in contacts]
        # jd_number = [x if x.wp_cnt is 0 else None for x in contacts]
        # unable_Sent = [x if x.wp_cnt is -1 else None for x in contacts]
        
        return jsonify({'con_all' : len(success_all)})
    except Exception as e:
        pass
        return "Naah" + str(e)
@app.route('/task_report/<job_id>' , methods = ['POST' , 'GET'])
def task_report(job_id):
    # Endpoint for full report for JOB and TASK Results
    # TO-DO for next release
    pass