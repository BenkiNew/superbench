# Завдання

Сервер, де змонтовано union-каталог `docs_union` (union-mount поверх
локальної гілки та віддаленого SFTP-сховища через rclone-подібний
процес), стабільно тримає 20–30% CPU на rclone-процесі й 5–9% на самому
union mount — годинами, без піків.

Дано:
- `fixture/suspects_timeline.txt` — хронологія розслідування: інженер
  підозрював два фонові обхідники дерева, призупинив обидва, CPU не
  змінився;
- `fixture/strace_rclone.txt` — `strace -c` на rclone-процес;
- `fixture/strace_mergerfs.txt` — `strace -c` на сам union-mount процес;
- `fixture/auditd_report.txt` — аудит на рівні системних викликів
  (`getxattr`/`lgetxattr`/`fgetxattr`) за 2-секундне вікно;
- `fixture/current_mount_unit.txt` — як union mount піднято зараз;
- `fixture/docs_excerpt.txt` — витяг з документації union-mount (не з
  `--help`).

Поясніть точний механізм: чому призупинення двох підозрюваних фонових
процесів (`fixture/suspects_timeline.txt`) не змінило навантаження, хто
насправді генерує системні виклики за `fixture/auditd_report.txt`, і чому
саме вони дають таке навантаження на CPU обох процесів. Наведіть точні
`fixture/<file>:рядок` докази. Запропонуйте точну мінімальну правку
конфігурації (з точним синтаксисом опції, не приблизно).
