from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_dashboard', '0009_alter_teacher_subj'),
        ('timetable', '0006_alter_academicclass_major'),
    ]

    operations = [

        # 1. Backup the old ForeignKey values
        migrations.RunSQL(
            sql="""
                CREATE TABLE teacher_subject_backup (
                    teacher_id VARCHAR(10),
                    subject_id BIGINT
                );
            """,
            reverse_sql="""
                DROP TABLE IF EXISTS teacher_subject_backup;
            """
        ),

        migrations.RunSQL(
            sql="""
                INSERT INTO teacher_subject_backup (teacher_id, subject_id)
                SELECT TrID, subj_id
                FROM admin_dashboard_teacher
                WHERE subj_id IS NOT NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # 2. Remove old ForeignKey
        migrations.RemoveField(
            model_name='teacher',
            name='subj',
        ),

        # 3. Add new ManyToMany field
        migrations.AddField(
            model_name='teacher',
            name='subj',
            field=models.ManyToManyField(
                blank=True,
                related_name='teachers',
                to='timetable.subject',
            ),
        ),

        # 4. Restore old relationships into M2M table
        migrations.RunSQL(
            sql="""
                INSERT INTO admin_dashboard_teacher_subj
                    (teacher_id, subject_id)
                SELECT teacher_id, subject_id
                FROM teacher_subject_backup;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # 5. Remove backup table
        migrations.RunSQL(
            sql="""
                DROP TABLE teacher_subject_backup;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),]
