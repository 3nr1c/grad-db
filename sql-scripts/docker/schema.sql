-- DEGREES

CREATE TABLE IF NOT EXISTS "degree" (
    "code" varchar NOT NULL PRIMARY KEY,
    "name" varchar
);


-- SUBJECTS

CREATE TABLE IF NOT EXISTS "subject" (
    "code" varchar NOT NULL PRIMARY KEY,
    "name" varchar NOT NULL,
    "credits" varchar DEFAULT '6'
);

CREATE TABLE IF NOT EXISTS "subject_year" (
    "subject_code" varchar NOT NULL REFERENCES subject(code),
    "year" int NOT NULL,
    "year_alias" varchar,
    "pla_docent" text,
    PRIMARY KEY ("subject_code", "year")
);


-- degree_subject(degree_code, subject_code, type, mention)

CREATE TABLE IF NOT EXISTS "degree_subject" (
    "degree_code" varchar NOT NULL REFERENCES degree(code),
    "subject_code" varchar NOT NULL REFERENCES subject(code),
    "type" varchar,
    "mention" varchar,
    PRIMARY KEY ("degree_code", "subject_code")
);

-- COMPETENCES

CREATE TABLE IF NOT EXISTS "competence" (
    "id" varchar NOT NULL PRIMARY KEY,
    "description" text
);

CREATE TABLE IF NOT EXISTS "subject_competence" (
    "subject_code" varchar NOT NULL REFERENCES subject(code),
    "competence_id" varchar NOT NULL REFERENCES competence(id),
    PRIMARY KEY ("subject_code","competence_id")
);


-- PROFESSORS & CLASS GROUPS

CREATE TABLE IF NOT EXISTS "professor" (
    "code" SERIAL PRIMARY KEY,
    "name" varchar NOT NULL,
    "department" varchar,
    "email" varchar
);

CREATE TABLE IF NOT EXISTS "class_group" (
    "id" SERIAL PRIMARY KEY,
    "subject_code" varchar NOT NULL,
    "year" int NOT NULL,
    "semester" varchar NOT NULL,
    "group" varchar NOT NULL,
    "schedule" text,
    "room" varchar,
    "language" varchar,
    FOREIGN KEY ("subject_code", "year") REFERENCES "subject_year"
);

CREATE TABLE IF NOT EXISTS "class_group_professor" (
    "class_group_id" integer REFERENCES class_group("id"),
    "professor_code" integer REFERENCES professor(code),
    PRIMARY KEY ("class_group_id", "professor_code")
);