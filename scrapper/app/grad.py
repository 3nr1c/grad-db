# coding=utf-8
import requests
from bs4 import BeautifulSoup
import psycopg2
from config import config
import re
from orm import Persistent
from hashlib import md5
import asyncio
from aiohttp import ClientSession, ClientTimeout, ClientConnectorError

timeoutSettings = ClientTimeout(total=5)

async def fetch(*args, **kwargs):
    sleep_time = 30
    while True:
        async with sem:
            try:
                    print(kwargs["url"][:80])

                    if "data" in kwargs:
                        print(str(kwargs["data"])[:80])
                    elif "params" in kwargs:
                        print(str(kwargs["params"])[:80])

                    async with ClientSession(timeout=timeoutSettings) as session:
                        async with session.request(*args, **kwargs) as page:
                            if page.status == 404:
                                return None
                            elif page.status >= 500:
                                continue
                            elif page.status != 200:
                                continue
                            else:
                                return await page.text()
            except ClientConnectorError:
                print("\nEXCEPTION\n")
                continue
            except asyncio.TimeoutError:
                print("TIMEOUT, SLEEPING {}s...".format(sleep_time))
                await asyncio.sleep(sleep_time)
                sleep_time += 30
                continue



async def scrap_plan(conn, degree_code, subject_code=None, year=None):
    pla_docent_url = "http://www.ub.edu/grad/plae/AccesInformePD"
    get_params = {
        "curs": year,
        "idioma": "CAT",
        "codiGiga": subject_code,
        "recurs": "publicacio"
    }

    try:
        pla_docent_text = await fetch(url=pla_docent_url, method="GET", params=get_params)
    except ClientConnectorError:
        print("\nException @scrap_plan!")
        print(degree_code)
        print(pla_docent_url)
        print(str(get_params))
        print()
        return

    year_alias = str(year) + "-" + str(year + 1)
    Persistent(conn, "subject_year", pkey=["subject_code", "year"],
               subject_code=subject_code,
               year=year,
               year_alias=year_alias,
               pla_docent=pla_docent_text)

    if pla_docent_text is None: return

    pla_docent_soup = BeautifulSoup(pla_docent_text, "html.parser")

    competencies = pla_docent_soup.find_all("table", class_="taulaCompetencies")

    for table in competencies:
        for tag in table.find_all("span"):
            if tag.string is not None:
                matching = re.match("([^.]{1,45})\s*\.\s*(.+)", tag.string.strip())
                try:
                    comp_id, comp_desc = matching.groups()
                except AttributeError:
                    comp_desc = tag.string
                    comp_id = md5(comp_desc.encode("utf-8")).hexdigest()

                Persistent(conn, "competence", pkey=["id"], id=comp_id, description=comp_desc)
                Persistent(conn, "subject_competence", subject_code=subject_code, competence_id=comp_id)


# http://www.ub.edu/grad/plae/AccesInformePD?curs=2018&codiGiga=364292&idioma=CAT&recurs=publicacio
async def fetch_professor(conn, degree_code, year, professor_code):
    directori_url = "http://www.ub.edu/grad/infes/fitxaInfe.jsp"
    post_params = {
        "n0": "P2L",
        "n1": "000",
        "n2": 1,
        "curs": year,
        "ens": degree_code,
        "prof": professor_code
    }

    try:
        directori_text = await fetch(url=directori_url, method="POST", data=post_params)
        if directori_text is None: return
    except ClientConnectorError:
        print("\nProfessor exception!\n")
        return

    dsoup = BeautifulSoup(directori_text, "html.parser")

    name = dsoup.select_one("td.titol_paginaPDI")
    email = dsoup.select_one("a[href^=mailto]")
    department = dsoup.select_one("td.titoltext3")

    if name is None:
        return
    else:
        name = name.text.strip()
        name = re.sub("(^[.,]|[.,]$)", "", name).strip()
        name = re.sub("\s+", " ", name).title()

    if email is not None: email = email.text.strip()
    if department is not None: department = department.text.strip()

    return Persistent(conn, "professor",
               pkey=["name"],
               update=True,
               name=name,
               department=department,
               email=email).result["code"]


async def scrap_schedule(conn, degree_code, subject_code, year, semester):
    semester = str(semester)
    horaris_url = "http://www.ub.edu/grad/infes/fitxaInfe.jsp"
    post_params = {
        "curs": year,
        "ens": degree_code,
        "assig": subject_code,
        "n0": "2L",
        "n1": "00",
        "n2": "1",
        "cicle": "g",
        "cursImp": "null",
        "grup": "null",
        "semImp": "null",
        "semIni": semester,
        "prof": "",
        "tipus": "FB",
        "ta": "null",
        "target": "_parent"
    }

    try:
        horaris_text = await fetch(url=horaris_url, method="POST", data=post_params)
        if horaris_text is None: return
    except ClientConnectorError:
        print("\nSchedule exception!\n")
        return

    horaris_soup = BeautifulSoup(horaris_text, "html.parser")

    for group in horaris_soup.find_all("div", class_="faGrup"):
        group_table = group.find("table", class_="faPlanifGrup")
        if group_table is None:  # skip headers & the like
            continue

        faDDGrup = group_table.find("td", class_="faDDGrup")
        schedule = group_table.find("table", class_="idh")
        profs = group_table.find("td", class_="cPlanif_Prof_M1")
        room = group_table.find("td", class_="cPlanif_Local_M1")
        language = group_table.find("td", class_="faDDIdioma")

        # Clean nullable columns
        if schedule is not None: schedule = str(schedule)
        if room is not None: room = room.text.strip()
        if language is not None: language = language.text.strip()

        # Clean variables
        class_group_id = None
        professor_code = None

        if faDDGrup is not None:
            class_group_id = Persistent(conn, "class_group",
                                        pkey=["subject_code", "year", "semester", "group"],
                                        subject_code=subject_code,
                                        year=year,
                                        semester=semester,
                                        group=faDDGrup.text.strip(),
                                        schedule=schedule,
                                        room=room,
                                        language=language).result["id"]

        if profs is not None:
            for professor in profs.find_all("a"):
                professor_code = re.search("fitxaProf\('(\d+)'\)", professor["href"])[1]
                professor_code = await fetch_professor(conn,
                                      degree_code=degree_code,
                                      year=year,
                                      professor_code=professor_code)


        if None not in [class_group_id, professor_code]:
            Persistent(conn, "class_group_professor",
                       class_group_id=class_group_id,
                       professor_code=professor_code)


async def scrap_subject(conn, degree_code=None, subject_code=None, year=None):
    # We need to scrap plans before schedule because of foreign key constraints in the database
    await scrap_plan(conn=conn, degree_code=degree_code, subject_code=subject_code, year=year)

    await asyncio.gather(
        asyncio.create_task(
            scrap_schedule(conn, degree_code=degree_code, subject_code=subject_code, year=year, semester=1)),
        asyncio.create_task(
            scrap_schedule(conn, degree_code=degree_code, subject_code=subject_code, year=year, semester=2))
    )


async def scrap_degree_year(conn, code, current_year, type):
    # get subject codes:
    subject_list_url = "http://www.ub.edu/grad/infes/fitxaInfe.jsp?n0=L&n1=0&n2=1&ens={}&curs={}&tipus={}" \
        .format(code, current_year, type)

    # http://www.ub.edu/grad/infes/fitxaInfe.jsp?n0=L&n1=0&n2=1&curs=2018&ens=TG1077

    try:
        subject_list_text = await fetch(url=subject_list_url, method="GET")
        if subject_list_text is None: return
    except ClientConnectorError as e:
        print(str(e))
        return

    subject_list_soup = BeautifulSoup(subject_list_text, "html.parser")
    degree_name = subject_list_soup.find("td", class_="titol_pagina").text.strip()
    if degree_name:
        Persistent(conn, "degree", pkey=["code"], code=code, name=degree_name)

    subject_tasks = []

    for tr in subject_list_soup.find_all("tr"):
        ioAssigCodi = tr.find("td", class_="ioAssigCodi")
        ioAssigDesc = tr.find("td", class_="ioAssigDesc")
        ioAssigCredits = tr.find("td", class_="ioAssigCredits")
        if None in [ioAssigCodi, ioAssigDesc, ioAssigCredits]:
            continue

        subject_code = ioAssigCodi.text.strip()

        Persistent(conn, "subject",
                   pkey=["code"],
                   code=subject_code,
                   name=ioAssigDesc.text.strip(),
                   credits=ioAssigCredits.text.strip())

        Persistent(conn, "degree_subject", pkey=["degree_code", "subject_code"],
                   degree_code=code,
                   subject_code=subject_code,
                   type=type)

        subject_tasks.append(
            asyncio.create_task(
                scrap_subject(conn=conn, degree_code=code, subject_code=subject_code, year=current_year)
            )
        )

    await asyncio.gather(*subject_tasks)


async def main():
    year_range = [2019, 2018, 2017]

    tasks = []
    for i in [1042, 1077]: # range(1000, 1110): # range(1077, 1078):
        for year in year_range:
            for type in ["FB", "OB", "OT", "TR", "PR"]:
                tasks.append(
                    asyncio.create_task(
                        scrap_degree_year(conn=conn, code="TG{}".format(i), current_year=year, type=type)
                    )
                )
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    params = config()
    conn = psycopg2.connect(**params)

    sem_tokens = input("Semaphore limit? (15) ")
    if sem_tokens == "":
        sem_tokens = 15
    sem = asyncio.Semaphore(int(sem_tokens))

    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())

    conn.close()
