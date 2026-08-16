-- All observed devices + registry labels (EN + ZH).
-- Real probe UUIDs stay unless marked noise. Labels are managed in seeds/device_registry.csv.

with observed as (
    select distinct device_id
    from {{ ref('stg_device_usage_hour') }}
),

seeded as (
    select
        device_id,
        display_name,
        display_name_zh,
        persona,
        site,
        is_demo_noise::boolean as is_demo_noise,
        notes
    from {{ ref('device_registry') }}
),

universe as (
    select device_id from observed
    union
    select device_id from seeded
)

select
    u.device_id,
    coalesce(s.display_name, u.device_id) as display_name,
    coalesce(
        nullif(trim(s.display_name_zh), ''),
        s.display_name,
        case
            when u.device_id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                then '未登记探针-' || left(u.device_id, 8)
            when u.device_id like 'sim-%' then '模拟设备-' || u.device_id
            else '未登记设备-' || u.device_id
        end
    ) as display_name_zh,
    coalesce(
        s.persona,
        case
            when u.device_id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                then 'probe'
            when u.device_id like 'sim-%' then 'simulator'
            else 'unknown'
        end
    ) as persona,
    coalesce(s.site, 'unregistered') as site,
    coalesce(s.is_demo_noise, false) as is_demo_noise,
    (not coalesce(s.is_demo_noise, false)) as include_in_demo,
    (s.device_id is not null) as in_registry,
    s.notes
from universe u
left join seeded s on s.device_id = u.device_id
