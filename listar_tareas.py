from celery import current_app

print('Tareas registradas:')
for task_name in sorted(current_app.tasks.keys()):
    if 'apps.generador_actas' in task_name:
        print(f'  - {task_name}')