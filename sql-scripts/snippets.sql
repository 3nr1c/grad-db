SELECT
	degree_code,
	degree.name AS degree_name,
	subject_code,
	TYPE AS subject_type,
	subject.name AS subject_name,
	credits
FROM
	degree
	JOIN degree_subject ON degree.code = degree_subject.degree_code
	JOIN subject ON degree_subject.subject_code = subject.code;

SELECT
	subject.name,
	class_group."group",
	professor.name
FROM
	subject
	JOIN class_group ON subject.code = class_group.subject_code
	JOIN class_group_professor ON class_group.id = class_group_professor.class_group_id
	JOIN professor ON professor.id = class_group_professor.professor_id;

SELECT
	subject.name AS subject_name,
	competence_id,
	competence.description,
	subject.code,
	subject_year.year_alias
FROM
	subject
	JOIN subject_competence ON subject.code = subject_competence.subject_code
	JOIN competence ON subject_competence.competence_id = competence.id
	JOIN subject_year ON subject.code = subject_year.subject_code
WHERE
	competence_id LIKE '7FC%';


SELECT 
	professor_l."name" AS professor1_name,
	professor_r."name" AS professor2_name,
	class_group_l.class_group_id
FROM
	professor professor_l
	JOIN class_group_professor class_group_l ON professor_l.code = class_group_l.professor_code
	JOIN class_group_professor class_group_r ON
		class_group_l.class_group_id = class_group_r.class_group_id
	JOIN professor professor_r ON class_group_r.professor_code = professor_r.code
WHERE
	class_group_l.professor_code < class_group_r.professor_code;


SELECT
	professor_l.code AS source,
	professor_r.code AS target,
	class_group_l.subject_code,
	class_group_l."year",
	class_group_l.semester
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
		class_group_r.id = class_group_professor_r.class_group_id AND
		class_group_professor_l.class_group_id = class_group_professor_r.class_group_id
	JOIN professor professor_r ON class_group_professor_r.professor_code = professor_r.code
WHERE
	class_group_professor_l.professor_code < class_group_professor_r.professor_code;

-- GROUP PROFESSORS BY SUBJECT TERMS!!
SELECT
	professor_l.code AS source,
	professor_r.code AS target,
	class_group_l.subject_code,
	class_group_l."year",
	class_group_l.semester
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
WHERE
	class_group_professor_l.professor_code < class_group_professor_r.professor_code;