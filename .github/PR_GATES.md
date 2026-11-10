# Перевірка перед злиттям

Наявний CI `test` зберігається. Перед злиттям кожного PR потрібні
успішна перевірка на поточному head. CodeRabbit знято 10.11.2026: новий огляд не вимагається.

Після перевіреного запуску виконавець налаштовує й повторно читає через API:

- required `test` від GitHub Actions (integration_id/app_id 15368); точний context й джерело обов’язкові;
- strict=true (у rulesets strict_required_status_checks_policy=true),
  актуальність гілки та результати саме поточного head;
- Require conversation resolution before merging
  (required_review_thread_resolution=true у rulesets);
- PR перед злиттям, заборону force-push і видалення основної гілки;
- enforcement=active та порожній bypass_actors у rulesets;
  для класичного захисту enforce_admins.enabled=true,
  allow_force_pushes.enabled=false, allow_deletions.enabled=false.

Далі перевіряє фактичне закриття поточних тредів та відсутність відкритих
залежних PR. Налаштування не підміняє виконаний CI або огляд. Код, дані,
пакети й розгортання цим документом не змінюються.
