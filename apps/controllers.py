# -*- coding: utf-8 -*-
from .kstime import kstime, ksdate
from .upload_image import upload_image
from flask import render_template, request, redirect, url_for, flash, g, session, jsonify, make_response, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import desc,distinct,func, select, and_
from sqlalchemy.orm import contains_eager,load_only
from sqlalchemy.orm.exc import NoResultFound
from apps import app, db
import datetime
import uuid
import json
import humanize

import logging
from werkzeug.http import parse_options_header

from apps.models import (
    Stranger, Ca, Rel_participant
)

# 메일발송
from .mail import sender



@app.before_request
def before_request():
    if 'stranger_name' in session:
        g.stranger_name = session['stranger_name']
        g.stranger_id = session['stranger_id']
        g.stranger_color = session['stranger_color']
    if 'stranger_notion' in session:
        g.stranger_notion = session['stranger_notion']
    if 'stranger_position' in session:
        g.stranger_position = session['stranger_position']




@app.route('/', methods=['GET'])
def index():
    return render_template('/index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():

    if 'stranger_name' in session:

        return redirect(url_for('ca_list'))

    else:

        if request.method == 'GET':

            return render_template('/login.html')

        elif request.method == 'POST':

            user_data = request.form
            phone = user_data['phone']
            password = user_data['password']

            try:
                stranger = db.session.query(Stranger).filter(Stranger.phone==phone).one()

                if stranger.password == "":
                    stranger.password = generate_password_hash(password)
                    db.session.commit() 

                if not check_password_hash(stranger.password, password):
                    flash(u'비밀번호가 올바르지 않습니다.', 'danger')
                    return redirect(url_for('login'))

                else:

                    session.permanent = True
                    session['stranger_id'] = stranger.id
                    session['stranger_name'] = stranger.name
                    session['stranger_color'] = stranger.color
                    session['stranger_notion'] = stranger.notion_url
                    if stranger.position == "staff":
                        session['stranger_position'] = stranger.position
                    return redirect(url_for('ca_list'))

            except NoResultFound as e:
                flash(u'낯선대학y6 멤버가 아닌 것 같아요.', 'danger')
                return redirect(url_for('login'))




@app.route('/ca/list', methods=['GET', 'POST'])
def ca_list():

    if not 'stranger_name' in session:
        flash(u'로그인이 필요합니다.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'GET':

        stranger = Stranger.query.get(g.stranger_id)

        # 나의 참여횟수

        my_participate = {}
        my_participate['ongoing'] = db.session.query(Rel_participant)\
                .filter(Rel_participant.stranger_id == g.stranger_id)\
                .outerjoin(Ca, Ca.id == Rel_participant.ca_id)\
                .filter(Ca.date >= ksdate(9))\
                .count()
        my_participate['close'] = db.session.query(Rel_participant)\
                .filter(Rel_participant.stranger_id == g.stranger_id)\
                .outerjoin(Ca, Ca.id == Rel_participant.ca_id)\
                .filter(Ca.date < ksdate(9))\
                .count()


        # 종료된 모임
        ca_done = []

        stmt_1 = db.session.query(Rel_participant.ca_id, func.count('*').label('people_count'))\
                .group_by(Rel_participant.ca_id).subquery()

        for u, count in db.session.query(Ca, stmt_1.c.people_count)\
                .outerjoin(stmt_1, Ca.id==stmt_1.c.ca_id)\
                .filter(Ca.date < ksdate(9))\
                .order_by(desc(Ca.date)):
            ca_done.append([u, count])

        # 모집중인 모임
        ca_ongoing = []

        stmt_2 = db.session.query(Rel_participant.ca_id, func.count('*').label('people_count'))\
                .group_by(Rel_participant.ca_id).subquery()

        for u, count in db.session.query(Ca, stmt_2.c.people_count)\
                .outerjoin(stmt_2, Ca.id==stmt_2.c.ca_id)\
                .filter(Ca.date >= ksdate(9))\
                .filter(stmt_2.c.people_count < Ca.people)\
                .order_by(Ca.date):
            ca_ongoing.append([u, count])
        
        # 모집완료 모임
        ca_close = []

        stmt_3 = db.session.query(Rel_participant.ca_id, func.count('*').label('people_count'))\
                .group_by(Rel_participant.ca_id).subquery()

        for u, count in db.session.query(Ca, stmt_3.c.people_count)\
                .outerjoin(stmt_3, Ca.id==stmt_3.c.ca_id)\
                .filter(Ca.date >= ksdate(9))\
                .filter(stmt_3.c.people_count >= Ca.people)\
                .order_by(Ca.date):
            ca_close.append([u, count])


        return render_template('/ca-list.html', stranger=stranger, ca_done=ca_done, ca_ongoing=ca_ongoing, ca_close=ca_close, my_participate=my_participate)


@app.route('/ca/create', methods=['GET', 'POST'])
def ca_create():

    if not 'stranger_name' in session:
        flash(u'로그인이 필요합니다.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'GET':

        return render_template('/ca-create.html', today = ksdate(9))

    elif request.method == 'POST':

        form_data = request.form

        ca = Ca(
            title = form_data['title'],
            date = form_data['date'],
            people = form_data['people'],
            description = form_data['description'],
            stranger_id = g.stranger_id,
            date_created = kstime(9),
            date_edited = kstime(9)
        )

        db.session.add(ca)
        db.session.flush()

        rel_participant = Rel_participant(
            stranger_id = g.stranger_id,
            ca_id = ca.id,
            date_created = kstime(9),
        )

        db.session.add(rel_participant)
        db.session.commit()

        # 알림 이메일 발송

        title = "새로운 모임이 만들어졌습니다!"
        content = """
        <html>
            <body>
                <h2><span style="font-size: 2em;">🎉</span><br>낯선대학y6에<br>새로운 모임이 만들어졌습니다!</h2>
                <br>
                <p><b>모임명 :</b> """ + ca.title + """</p>
                <p><b>개설자 :</b> """ + ca.stranger.name + """</p>
                <br>
                <p><span style="font-size: 1.3em;">🕵️‍♂️</span><br>자세한 모임 내용이 궁금하다면<br>아래의 링크를 클릭해 웹사이트에서 확인해보세요.</p>
                <a href="https://hi-stranger.yonghyun.kr/ca/""" + str(ca.id) + """">웹사이트에서 자세히 보기</a>
            </body>
        </html>
        """

        recipients = db.session.query(Stranger).all()

        serialized_recipients = [
            {
                "email": object.email,
            } for object in recipients
        ]

        sender(serialized_recipients, title, content)
        

        return redirect(url_for('ca_made', id=ca.id,))



@app.route('/ca/edit/<int:id>', methods=['GET', 'POST'])
def ca_edit(id):

    if not 'stranger_name' in session:
        flash(u'로그인이 필요합니다.', 'danger')
        return redirect(url_for('index'))

    ca = Ca.query.get(id)

    if request.method == 'GET':

        return render_template('/ca-edit.html', ca=ca, today = ksdate(9))

    elif request.method == 'POST':

        form_data = request.form

        ca.title = form_data['title']
        ca.date = form_data['date']
        ca.people = form_data['people']
        ca.description = form_data['description']
        ca.date_edited = kstime(9)

        db.session.commit()

        # 알림 이메일 발송

        title = "모임 내용이 수정되었습니다!"
        content = """
        <html>
            <body>
                <h2><span style="font-size: 2em;">🎉</span><br>기존에 신청하신 모임의 내용이<br>아래와 같이 수정되었습니다.</h2>
                <br>
                <p><b>모임명 :</b> """ + ca.title + """</p>
                <p><b>개설자 :</b> """ + ca.stranger.name + """</p>
                <p><b>모임 예정일 :</b> """ + str(ca.date.strftime('%Y-%m-%d')) + """</p>
                <p><b>최대 참여 인원 :</b> """ + str(ca.people) + """</p>
                <p><b>개설자 한마디 :</b><br> """ + ca.description + """</p>
                <br>
                <p><span style="font-size: 1.3em;">🕵️‍♂️</span><br>웹사이트에서 내용을 확인하려면<br>아래의 링크를 클릭해 보세요.</p>
                <a href="https://hi-stranger.yonghyun.kr/ca/""" + str(ca.id) + """">웹사이트에서 자세히 보기</a>
            </body>
        </html>
        """

        recipients = db.session.query(Rel_participant)\
                .filter(Rel_participant.ca_id==ca.id)

        serialized_recipients = [
            {
                "email": object.stranger.email,
            } for object in recipients
        ]

        sender(serialized_recipients, title, content)
        

        return redirect(url_for('ca_detail', id=ca.id,))



@app.route('/ca/<int:id>', methods=['GET', 'POST'])
def ca_detail(id):

    if not 'stranger_name' in session:
        flash(u'로그인이 필요합니다.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'GET':

        ca = Ca.query.get(id)

        participants = db.session.query(Rel_participant)\
                .filter(Rel_participant.ca_id == id)\
                .order_by(Rel_participant.date_created)

        my_status = db.session.query(Rel_participant)\
            .filter(Rel_participant.stranger_id==g.stranger_id, Rel_participant.ca_id==id)\
            .first()

        count = db.session.query(Rel_participant)\
            .filter(Rel_participant.ca_id==id)\
            .count()

        # remain_day = ca.date - ksdate(9)
        _t = humanize.i18n.activate("KO")
        remain_day = humanize.naturaldelta(ca.date - ksdate(9))
        

        return render_template('/ca-detail.html', ca=ca, participants=participants, my_status=my_status,count=count, today = kstime(9), remain_day=remain_day)


@app.route('/ca/made/<int:id>', methods=['GET', 'POST'])
def ca_made(id):

    if not 'stranger_name' in session:
        flash(u'로그인이 필요합니다.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'GET':

        ca = Ca.query.get(id)

        return render_template('/ca-made.html', ca=ca, today = kstime(9))




@app.route('/ca/join', methods=['GET', 'POST'])
def ca_join():

    if not 'stranger_name' in session:
        flash(u'로그인이 필요합니다.', 'danger')
        return redirect(url_for('index'))

    ca_id = request.form['ca_id']
    stranger_id = request.form['stranger_id']

    try:

        rel_participant = db.session.query(Rel_participant)\
                .filter(Rel_participant.stranger_id==stranger_id, Rel_participant.ca_id==ca_id)\
                .one()


    except NoResultFound as e:
        
        rel_participant = Rel_participant(
            stranger_id = stranger_id,
            ca_id = ca_id,
            date_created = kstime(9),
        )

        db.session.add(rel_participant)
        db.session.commit()



        # 알림 이메일 발송

        title = "새로운 멤버가 모임에 참여했어요!"
        content = """
        <html>
            <body>
                <h2><span style="font-size: 2em;">🔥</span><br>내가 참여한 모임에<br>새로운 멤버가 참여했습니다.</h2>
                <br>
                <p><b>모임명 :</b> """+rel_participant.ca.title+"""</p>
                <p><b>개설자 :</b> """+rel_participant.ca.stranger.name+"""</p>
                <br>
                <p><b>신규 참여자 :</b> """+rel_participant.stranger.name+"""</p>
                <br>
                <p><span style="font-size: 1.3em;">🕵️‍♂️</span><br>자세한 내용이 궁금하다면<br>아래의 링크를 클릭해 웹사이트에서 확인해보세요.</p>
                <a href="https://hi-stranger.yonghyun.kr/ca/"""+str(rel_participant.ca.id)+"""">웹사이트에서 자세히 보기</a>
            </body>
        </html>
        """

        recipients = db.session.query(Rel_participant)\
                .filter(Rel_participant.ca_id==ca_id, Rel_participant.ca_id!=g.stranger_id)


        serialized_recipients = [
            {
                "email":  object.stranger.email,
            } for object in recipients
        ]

        sender(serialized_recipients, title, content)
    


        return stranger_id


@app.route('/ca/unjoin', methods=['GET', 'POST'])
def ca_unjoin():

    if not 'stranger_name' in session:
        flash(u'로그인이 필요합니다.', 'danger')
        return redirect(url_for('index'))

    ca_id = request.form['ca_id']
    stranger_id = request.form['stranger_id']

    participation = db.session.query(Rel_participant)\
            .filter(Rel_participant.stranger_id==stranger_id, Rel_participant.ca_id==ca_id)\
            .first()

    db.session.delete(participation)
    db.session.commit()

    return stranger_id



@app.route('/ca/delete', methods=['GET', 'POST'])
def ca_delete():

    if not 'stranger_name' in session:
        flash(u'로그인이 필요합니다.', 'danger')
        return redirect(url_for('index'))

    ca_id = request.form['ca_id']
    stranger_id = request.form['stranger_id']

    ca = Ca.query.get(ca_id)

    if g.stranger_id == ca.stranger_id:
        db.session.delete(ca)
        db.session.commit()

    return stranger_id




@app.route('/registration', methods=['GET'])
def registration_index():
    return render_template('/registration/index.html')



@app.route('/registration/01', methods=['GET', 'POST'])
def registration_step_01():

    if request.method == 'GET':

        return render_template('/registration/step-01.html')

    elif request.method == 'POST':


        get_data = request.form
        phone = get_data['phone']

        try:
            stranger = db.session.query(Stranger).filter(Stranger.phone == phone).one()
            session.permanent = True
            session['stranger_id'] = stranger.id

            return redirect(url_for('registration_step_02'))

        except NoResultFound:

            flash(u'등록되어있지 않은 전화번호 입니다', 'danger')
                
            return redirect(url_for('registration_step_01'))


@app.route('/registration/02', methods=['GET', 'POST'])
def registration_step_02():

    # if not 'stranger_id' in session:
    #     flash(u'잘못된 접근입니다.', 'danger')
    #     return redirect(url_for('index'))

    stranger = Stranger.query.get(g.stranger_id)

    if request.method == 'GET':

        return render_template('/registration/step-02.html', stranger=stranger)

    elif request.method == 'POST':

        stranger.privacy_agree = kstime(9)
        stranger.date_edited = kstime(9)
        db.session.commit()

        return redirect(url_for('registration_step_03'))
   

@app.route('/registration/03', methods=['GET', 'POST'])
def registration_step_03():

    if not 'stranger_id' in session:
        flash(u'잘못된 접근입니다.', 'danger')
        return redirect(url_for('index'))

    stranger = Stranger.query.get(g.stranger_id)

    if request.method == 'GET':

        return render_template('/registration/step-03.html', stranger=stranger)

    elif request.method == 'POST':

        get_data = request.form

        stranger.name = get_data['name']
        stranger.email = get_data['email']
        stranger.date_edited = kstime(9)

        db.session.commit()

        return redirect(url_for('registration_step_04'))


@app.route('/registration/04', methods=['GET', 'POST'])
def registration_step_04():

    if not 'stranger_id' in session:
        flash(u'잘못된 접근입니다.', 'danger')
        return redirect(url_for('index'))

    stranger = Stranger.query.get(g.stranger_id)

    if request.method == 'GET':

        return render_template('/registration/step-04.html', stranger=stranger)

    elif request.method == 'POST':

        get_data = request.form

        stranger.attendance = get_data['attendance']
        stranger.date_edited = kstime(9)

        db.session.commit()

        return redirect(url_for('registration_step_05'))


@app.route('/registration/05', methods=['GET', 'POST'])
def registration_step_05():

    if not 'stranger_id' in session:
        flash(u'잘못된 접근입니다.', 'danger')
        return redirect(url_for('index'))

    stranger = Stranger.query.get(g.stranger_id)

    if request.method == 'GET':

        return render_template('/registration/step-05.html', stranger=stranger)

    elif request.method == 'POST':

        get_data = request.form

        stranger.color = get_data['color']
        stranger.date_edited = kstime(9)

        db.session.commit()

        return redirect(url_for('registration_step_06'))

@app.route('/registration/06', methods=['GET', 'POST'])
def registration_step_06():

    if not 'stranger_id' in session:
        flash(u'잘못된 접근입니다.', 'danger')
        return redirect(url_for('index'))

    stranger = Stranger.query.get(g.stranger_id)

    if request.method == 'GET':

        return render_template('/registration/step-06.html', stranger=stranger)

    elif request.method == 'POST':

        session.clear()
        return redirect(url_for('registration_index'))


@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@app.route('/logout')
def log_out():
    session.clear()
    return redirect(url_for('index'))




@app.route('/network_stranger', methods=['GET', 'POST'])
def network_stranger():

    if not 'stranger_id' in session:
        flash(u'잘못된 접근입니다.', 'danger')
        return redirect(url_for('index'))

    return render_template('/network_stranger.html')

@app.route('/network_stranger_json', methods=['GET', 'POST'])
def network_stranger_json():

    nodes = []
    links = []

    strager_q = db.session.query(Stranger)\
                    .order_by(Stranger.name)
                    
    for strager in strager_q:
        strager_row = {}
        strager_row["id"] = strager.name
        if strager.name == g.stranger_name:
            strager_row["group"] = 2
        else:
            strager_row["group"] = 1
        nodes.append(strager_row)


    source_q = db.session.query(Rel_participant)\
                .outerjoin(Ca, Ca.id == Rel_participant.ca_id)\
                .filter(Ca.date < ksdate(9))\
                .order_by(Rel_participant.ca_id)



    for source in source_q:

        targets = []
        target_q = db.session.query(Rel_participant)\
                    .filter(Rel_participant.ca_id == source.ca.id)

        for target in target_q:

            if source.stranger.name != target.stranger.name:
            
                check_dict = {
                                "value": source.ca.id, 
                                "source": target.stranger.name, 
                                "target": source.stranger.name
                            }

                if check_dict not in links:
                    target_row = {}
                    target_row["value"] = source.ca.id
                    target_row["source"] = source.stranger.name
                    target_row["target"] = target.stranger.name
                    links.append(target_row)


    return jsonify(links=links, nodes=nodes)


#
# @error Handlers
#


# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404


# Handle 500 errors
@app.errorhandler(500)
def server_error(e):
	return render_template('500.html'), 500
