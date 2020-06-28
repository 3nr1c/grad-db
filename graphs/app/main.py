from flask import Flask, send_from_directory, jsonify, request
from config import config
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__, static_url_path='/static')


@app.route("/")
def hello():
    return app.send_static_file("index.html")


@app.route("/js/<file>")
def javascript(file):
    return app.send_static_file("js/" + file)


@app.route("/degrees.json")
def degree_list():
    if "heroku" in os.environ:
        return app.send_static_file("json/degrees.json")

    params = config()
    conn = psycopg2.connect(**params)

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT code, name FROM degree ORDER BY code ASC")

    ret = [dict(x) for x in cur.fetchall()]

    conn.commit()
    cur.close()
    conn.close()

    return jsonify(ret)


@app.route("/degree/<degree_code>/professors.json")
def fetch_degree(degree_code):
    if "heroku" in os.environ:
        return app.send_static_file("json/degree/" + degree_code + "/nodes_links.json")

    try:
        from_year = int(request.args.get("from_year"))
    except TypeError:
        from_year = 0

    try:
        to_year = int(request.args.get("to_year"))
    except TypeError:
        to_year = 10000

    return jsonify({
        "nodes": _fetch_professors(degree_code, from_year=from_year, to_year=to_year),
        "links": _fetch_professor_links(degree_code, from_year=from_year, to_year=to_year)
    })


def _fetch_professors(degree_code=None, from_year=0, to_year=10000):
    params = config()
    conn = psycopg2.connect(**params)

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    node_query = """
        SELECT 
            professor.code as id,
            professor.name as name,
            professor.department as department,
            array_agg(DISTINCT concat(class_group.year, ' ', subject.name)) as "extra_list"
        FROM 
            professor
        JOIN class_group_professor ON professor.code = class_group_professor.professor_code
        JOIN class_group ON class_group.id = class_group_professor.class_group_id
        JOIN subject ON subject.code = class_group.subject_code
        JOIN degree_subject ON degree_subject.subject_code = subject.code 
    """

    node_query += " WHERE class_group.year BETWEEN %s AND %s"

    query_arguments = [from_year, to_year]

    if degree_code is not None:
        node_query += " AND degree_subject.degree_code = %s"
        query_arguments.append(degree_code)

    node_query += " GROUP BY professor.code"
    cur.execute(node_query, query_arguments)

    ret = [dict(x) for x in cur.fetchall()]

    conn.commit()
    cur.close()
    conn.close()
    return ret


def _fetch_professor_links(degree_code=None, from_year=0, to_year=10000):
    params = config()
    conn = psycopg2.connect(**params)

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    link_query = """
    SELECT DISTINCT
        professor_l.code AS source,
        professor_r.code AS target,
        COUNT(*) AS strength
    FROM
        professor professor_l
        JOIN class_group_professor class_group_professor_l ON professor_l.code = class_group_professor_l.professor_code
        JOIN class_group class_group_l ON class_group_professor_l.class_group_id = class_group_l.id
        JOIN class_group class_group_r
            ON
                class_group_l.subject_code = class_group_r.subject_code AND
                class_group_l."year" = class_group_r."year" AND
                class_group_l.semester = class_group_r.semester
        JOIN class_group_professor class_group_professor_r ON
            class_group_r.id = class_group_professor_r.class_group_id
        JOIN professor professor_r ON class_group_professor_r.professor_code = professor_r.code
        JOIN subject ON subject.code = class_group_r.subject_code
        JOIN degree_subject ON degree_subject.subject_code = subject.code
    WHERE
        class_group_professor_l.professor_code < class_group_professor_r.professor_code 
        AND class_group_l."group" NOT IN ('Final', 'Reaval', '1r parc', 'G1')
        AND class_group_r."group" NOT IN ('Final', 'Reaval', '1r parc', 'G1')
        AND class_group_l.year BETWEEN %s AND %s
        {}
    GROUP BY source, target
    """

    query_arguments = [from_year, to_year]

    if degree_code is not None:
        link_query = link_query.format(" AND degree_subject.degree_code = %s")
        query_arguments.append(degree_code)
    else:
        link_query = link_query.format("")

    cur.execute(link_query, query_arguments)

    ret = [dict(x) for x in cur.fetchall()]

    conn.commit()
    cur.close()
    conn.close()
    return ret


@app.route("/degree/<degree_code>/subjects.json")
def fetch_subjects(degree_code):
    if "heroku" in os.environ:
        return app.send_static_file("json/subjects/" + degree_code + "/nodes_links.json")

    try:
        k = int(request.args.get("k"))
    except:
        pass
    finally:
        if k < 1:
            k = 1

    return jsonify({
        "nodes": _fetch_subjects(degree_code),
        "links": _fetch_subject_links(degree_code, k=k)
    })


def _fetch_subjects(degree_code=None):
    params = config()
    conn = psycopg2.connect(**params)

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    node_query = """
        SELECT DISTINCT 
            subject.code as id,
            subject.name as name,
            degree_subject.type as type,
            array_agg(competence.description) as "extra_list"
        FROM 
            degree_subject
            JOIN subject ON degree_subject.subject_code = subject.code
            JOIN subject_competence ON subject.code = subject_competence.subject_code
            JOIN competence ON subject_competence.competence_id = competence.id
        """

    if degree_code is not None:
        node_query += " WHERE degree_subject.degree_code = %s"
        node_query += " GROUP BY subject.code, degree_subject.type"
        cur.execute(node_query, [degree_code])
    else:
        node_query += " GROUP BY subject.code, degree_subject.type"
        cur.execute(node_query)

    ret = [dict(x) for x in cur.fetchall()]

    conn.commit()
    cur.close()
    conn.close()
    return ret


def _fetch_subject_links(degree_code=None, k=1):
    params = config()
    conn = psycopg2.connect(**params)

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    link_query = """
        SELECT 
            subject_l.code AS source,
            subject_r.code AS target,
            subject_l.name AS source_name,
            subject_r.name AS target_name,
            COUNT(*) AS strength
        FROM 
            degree_subject degree_subject_l
            JOIN subject subject_l ON degree_subject_l.subject_code = subject_l.code
            JOIN subject_competence subject_competence_l ON subject_l.code = subject_competence_l.subject_code
            JOIN subject_competence subject_competence_r ON 
                subject_competence_l.competence_id = subject_competence_r.competence_id 
            JOIN subject subject_r ON subject_competence_r.subject_code = subject_r.code
            JOIN degree_subject degree_subject_r ON subject_r.code = degree_subject_r.subject_code
        WHERE 
            degree_subject_l.degree_code = degree_subject_r.degree_code
            AND subject_l.code < subject_r.code 
            {}
        GROUP BY source, target 
        HAVING 
            COUNT(*) > 1 AND
            COUNT(subject_competence_l.competence_id) >= {}
        """

    # todo: filter with a NOT IT (other query)

    if degree_code is not None:
        link_query = link_query.format(" AND degree_subject_l.degree_code = %s", k)
        cur.execute(link_query, [degree_code])
    else:
        cur.execute(link_query.format(""))

    ret = [dict(x) for x in cur.fetchall()]

    conn.commit()
    cur.close()
    conn.close()
    return ret
