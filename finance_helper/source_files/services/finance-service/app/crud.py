"""Модуль финансового сервиса Finance Helper."""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, aliased

from . import models

DEFAULT_EXPENSE_CATEGORIES = [
    ("Еда", "🍔", ["еда", "продукты", "кафе", "ресторан", "пицца", "кофе", "обед", "ужин", "завтрак", "суши", "тако", "бургер"]),
    ("Транспорт", "🚇", ["такси", "метро", "автобус", "транспорт", "бензин", "парковка", "uber", "bolt"]),
    ("Дом", "🏠", ["дом", "аренда", "квартира", "коммунал", "ремонт", "икеа", "мебель"]),
    ("Развлечения", "🎉", ["кино", "бар", "игра", "развлеч", "концерт", "театр", "музей"]),
    ("Здоровье", "💊", ["аптека", "врач", "здоров", "лекар", "стоматолог"]),
    ("Образование", "📚", ["курс", "обучение", "книга", "урок", "школа", "универ", "образование"]),
    ("Другое", "🧾", ["другое", "прочее"]),
]

DEFAULT_INCOME_CATEGORIES = [
    ("Зарплата", "💼", ["зарплата", "зп", "salary", "оклад"]),
    ("Премия", "🎁", ["премия", "bonus", "бонус"]),
    ("Продажа вещей", "💸", ["продажа", "авито", "вещи", "продал", "продала"]),
    ("Подарки", "🎉", ["подарок", "подарили", "дарение"]),
    ("Другое", "🧾", []),
]


def _normalize_alias(value: str) -> str:
    """Выполняет действие «normalize alias» в рамках логики Finance Helper."""
    return " ".join(value.lower().strip().split())


def get_user(db: Session, telegram_id: int) -> models.User | None:
    """Возвращает данные для сценария «user»."""
    return db.scalar(select(models.User).where(models.User.telegram_id == telegram_id))


def _get_user_or_raise(db: Session, telegram_id: int) -> models.User:
    """Выполняет действие «get user or raise» в рамках логики Finance Helper."""
    user = get_user(db, telegram_id)
    if not user:
        raise ValueError("user_not_found")
    return user


def _get_personal_workspace(db: Session, user_id: int) -> models.Workspace | None:
    """Выполняет действие «get personal workspace» в рамках логики Finance Helper."""
    return db.scalar(
        select(models.Workspace)
        .where(models.Workspace.owner_user_id == user_id, models.Workspace.type == models.WorkspaceType.personal)
        .order_by(models.Workspace.id.asc())
    )


def _seed_default_categories(db: Session, workspace: models.Workspace, created_by_user_id: int) -> None:
    """Выполняет действие «seed default categories» в рамках логики Finance Helper."""
    for name, emoji, aliases in DEFAULT_EXPENSE_CATEGORIES:
        category = models.Category(
            workspace_id=workspace.id,
            created_by_user_id=created_by_user_id,
            name=name,
            type=models.OperationType.expense,
            emoji=emoji,
        )
        db.add(category)
        db.flush()
        for alias in aliases:
            db.add(
                models.CategoryAlias(
                    workspace_id=workspace.id,
                    category_id=category.id,
                    alias=alias,
                    normalized_alias=_normalize_alias(alias),
                )
            )

    for name, emoji, aliases in DEFAULT_INCOME_CATEGORIES:
        category = models.Category(
            workspace_id=workspace.id,
            created_by_user_id=created_by_user_id,
            name=name,
            type=models.OperationType.income,
            emoji=emoji,
        )
        db.add(category)
        db.flush()
        for alias in aliases:
            db.add(
                models.CategoryAlias(
                    workspace_id=workspace.id,
                    category_id=category.id,
                    alias=alias,
                    normalized_alias=_normalize_alias(alias),
                )
            )


def _ensure_personal_workspace(db: Session, user: models.User) -> models.Workspace:
    """Выполняет действие «ensure personal workspace» в рамках логики Finance Helper."""
    workspace = _get_personal_workspace(db, user.id)
    if workspace:
        if user.active_workspace_id is None:
            user.active_workspace_id = workspace.id
            db.flush()
        return workspace

    workspace = models.Workspace(
        owner_user_id=user.id,
        name="Личный бюджет",
        type=models.WorkspaceType.personal,
        base_currency=user.base_currency,
    )
    db.add(workspace)
    db.flush()

    db.add(models.WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=models.MemberRole.owner))
    _seed_default_categories(db, workspace, user.id)
    db.flush()
    if user.active_workspace_id is None:
        user.active_workspace_id = workspace.id
        db.flush()
    return workspace


def upsert_user(db: Session, telegram_id: int, username: str | None) -> models.User:
    """Выполняет действие «upsert user» в рамках логики Finance Helper."""
    user = get_user(db, telegram_id)
    if user:
        if username:
            user.username = username
        personal = _ensure_personal_workspace(db, user)
        if user.active_workspace_id is None:
            user.active_workspace_id = personal.id
        db.commit()
        db.refresh(user)
        return user

    user = models.User(telegram_id=telegram_id, username=username)
    db.add(user)
    db.flush()
    personal = _ensure_personal_workspace(db, user)
    if user.active_workspace_id is None:
        user.active_workspace_id = personal.id
    db.commit()
    db.refresh(user)
    return user


def get_user_by_username(db: Session, username: str) -> models.User | None:
    """Возвращает данные для сценария «user by username»."""
    normalized = username.strip().lstrip("@").lower()
    if not normalized:
        return None
    return db.scalar(
        select(models.User).where(func.lower(models.User.username) == normalized)
    )


def resolve_user_by_identifier(db: Session, identifier: str) -> models.User:
    """Выполняет действие «resolve user by identifier» в рамках логики Finance Helper."""
    value = identifier.strip()
    if not value:
        raise ValueError("member_identifier_invalid")

    if value.isdigit():
        user = get_user(db, int(value))
        if not user:
            raise ValueError("user_not_found")
        return user

    username = value.lstrip("@").strip()
    if not username:
        raise ValueError("member_identifier_invalid")

    user = get_user_by_username(db, username)
    if not user:
        raise ValueError("member_user_not_found")
    return user


def _membership_for_user(db: Session, workspace_id: int, user_id: int) -> models.WorkspaceMember | None:
    """Выполняет действие «membership for user» в рамках логики Finance Helper."""
    return db.scalar(
        select(models.WorkspaceMember).where(
            models.WorkspaceMember.workspace_id == workspace_id,
            models.WorkspaceMember.user_id == user_id,
        )
    )


def resolve_workspace_for_user(
    db: Session,
    telegram_id: int,
    workspace_id: int | None,
    require_write: bool = False,
) -> tuple[models.User, models.Workspace, models.WorkspaceMember]:
    """Выполняет действие «resolve workspace for user» в рамках логики Finance Helper."""
    user = _get_user_or_raise(db, telegram_id)
    if workspace_id is None:
        active_id = user.active_workspace_id
        workspace = db.get(models.Workspace, active_id) if active_id else None
        if workspace is None:
            workspace = _ensure_personal_workspace(db, user)
            user.active_workspace_id = workspace.id
            db.flush()
    else:
        workspace = db.get(models.Workspace, workspace_id)
    if not workspace:
        raise ValueError("workspace_not_found")

    membership = _membership_for_user(db, workspace.id, user.id)
    if not membership:
        raise ValueError("workspace_access_denied")

    if require_write and membership.role == models.MemberRole.viewer:
        raise ValueError("workspace_readonly")

    return user, workspace, membership


def list_workspaces(db: Session, telegram_id: int) -> list[models.Workspace]:
    """Возвращает список сущностей для сценария «workspaces»."""
    user = _get_user_or_raise(db, telegram_id)
    stmt = (
        select(models.Workspace)
        .join(models.WorkspaceMember, models.WorkspaceMember.workspace_id == models.Workspace.id)
        .where(models.WorkspaceMember.user_id == user.id)
        .order_by(models.Workspace.type.asc(), models.Workspace.id.asc())
    )
    return db.scalars(stmt).all()



def get_active_workspace(db: Session, telegram_id: int) -> models.Workspace:
    """Возвращает данные для сценария «active workspace»."""
    user = _get_user_or_raise(db, telegram_id)
    workspace = db.get(models.Workspace, user.active_workspace_id) if user.active_workspace_id else None
    if workspace and _membership_for_user(db, workspace.id, user.id):
        return workspace
    workspace = _ensure_personal_workspace(db, user)
    user.active_workspace_id = workspace.id
    db.commit()
    db.refresh(user)
    return workspace


def set_active_workspace(db: Session, telegram_id: int, workspace_id: int) -> models.Workspace:
    """Выполняет действие «set active workspace» в рамках логики Finance Helper."""
    user, workspace, _ = resolve_workspace_for_user(db, telegram_id, workspace_id)
    user.active_workspace_id = workspace.id
    db.commit()
    db.refresh(user)
    return workspace


def create_workspace(
    db: Session,
    telegram_id: int,
    name: str,
    workspace_type: models.WorkspaceType,
    base_currency: str,
) -> models.Workspace:
    """Создаёт сущность для сценария «workspace»."""
    owner = _get_user_or_raise(db, telegram_id)
    workspace = models.Workspace(
        owner_user_id=owner.id,
        name=name,
        type=workspace_type,
        base_currency=base_currency.upper(),
    )
    db.add(workspace)
    db.flush()

    db.add(models.WorkspaceMember(workspace_id=workspace.id, user_id=owner.id, role=models.MemberRole.owner))
    _seed_default_categories(db, workspace, owner.id)
    db.commit()
    db.refresh(workspace)
    return workspace


def add_workspace_member(
    db: Session,
    workspace_id: int,
    owner_telegram_id: int,
    member_telegram_id: int,
    role: models.MemberRole,
) -> models.WorkspaceMember:
    """Выполняет действие «add workspace member» в рамках логики Finance Helper."""
    _, workspace, membership = resolve_workspace_for_user(db, owner_telegram_id, workspace_id, require_write=True)
    if membership.role != models.MemberRole.owner:
        raise ValueError("owner_required")

    member_user = _get_user_or_raise(db, member_telegram_id)
    existing = _membership_for_user(db, workspace.id, member_user.id)
    if existing:
        existing.role = role
        db.commit()
        db.refresh(existing)
        return existing

    new_member = models.WorkspaceMember(workspace_id=workspace.id, user_id=member_user.id, role=role)
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member


def list_workspace_members(db: Session, telegram_id: int, workspace_id: int) -> list[models.WorkspaceMember]:
    """Возвращает список сущностей для сценария «workspace members»."""
    resolve_workspace_for_user(db, telegram_id, workspace_id)
    stmt = (
        select(models.WorkspaceMember)
        .where(models.WorkspaceMember.workspace_id == workspace_id)
        .order_by(models.WorkspaceMember.id.asc())
    )
    return db.scalars(stmt).all()


def update_workspace_member_role(
    db: Session,
    workspace_id: int,
    owner_telegram_id: int,
    member_telegram_id: int,
    role: models.MemberRole,
) -> models.WorkspaceMember:
    """Обновляет данные в сценарии «workspace member role»."""
    owner, workspace, membership = resolve_workspace_for_user(db, owner_telegram_id, workspace_id, require_write=True)
    if membership.role != models.MemberRole.owner:
        raise ValueError('owner_required')
    member_user = _get_user_or_raise(db, member_telegram_id)
    existing = _membership_for_user(db, workspace.id, member_user.id)
    if not existing:
        raise ValueError('member_not_found')
    if existing.user_id == owner.id:
        raise ValueError('owner_role_immutable')
    existing.role = role
    db.commit()
    db.refresh(existing)
    return existing


def remove_workspace_member(
    db: Session,
    workspace_id: int,
    owner_telegram_id: int,
    member_telegram_id: int,
) -> bool:
    """Удаляет сущность в сценарии «workspace member»."""
    owner, workspace, membership = resolve_workspace_for_user(db, owner_telegram_id, workspace_id, require_write=True)
    if membership.role != models.MemberRole.owner:
        raise ValueError('owner_required')
    member_user = _get_user_or_raise(db, member_telegram_id)
    existing = _membership_for_user(db, workspace.id, member_user.id)
    if not existing:
        return False
    if existing.user_id == owner.id:
        raise ValueError('owner_cannot_remove_self')
    db.delete(existing)
    db.commit()
    return True


# ---------- categories ----------


def list_categories(
    db: Session,
    telegram_id: int,
    workspace_id: int | None,
    category_type: models.OperationType | None = None,
    include_archived: bool = False,
) -> list[models.Category]:
    """Возвращает список сущностей для сценария «categories»."""
    _, workspace, _ = resolve_workspace_for_user(db, telegram_id, workspace_id)
    stmt = select(models.Category).where(models.Category.workspace_id == workspace.id)
    if category_type:
        stmt = stmt.where(models.Category.type == category_type)
    if not include_archived:
        stmt = stmt.where(models.Category.is_archived.is_(False))
    stmt = stmt.order_by(models.Category.type.asc(), models.Category.name.asc())
    return db.scalars(stmt).all()


def _get_category_by_name(
    db: Session,
    workspace_id: int,
    category_name: str,
    category_type: models.OperationType,
) -> models.Category | None:
    """Выполняет действие «get category by name» в рамках логики Finance Helper."""
    return db.scalar(
        select(models.Category).where(
            models.Category.workspace_id == workspace_id,
            models.Category.name == category_name,
            models.Category.type == category_type,
        )
    )


def create_category(
    db: Session,
    telegram_id: int,
    workspace_id: int | None,
    name: str,
    category_type: models.OperationType,
    emoji: str | None,
) -> models.Category:
    """Создаёт сущность для сценария «category»."""
    user, workspace, _ = resolve_workspace_for_user(db, telegram_id, workspace_id, require_write=True)
    existing = _get_category_by_name(db, workspace.id, name, category_type)
    if existing:
        if emoji and not existing.emoji:
            existing.emoji = emoji
            db.commit()
            db.refresh(existing)
        return existing

    category = models.Category(
        workspace_id=workspace.id,
        created_by_user_id=user.id,
        name=name,
        type=category_type,
        emoji=emoji,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(
    db: Session,
    telegram_id: int,
    category_id: int,
    name: str | None,
    emoji: str | None,
    is_archived: bool | None,
) -> models.Category:
    """Обновляет данные в сценарии «category»."""
    category = _get_category_or_raise(db, category_id)
    _, workspace, _ = resolve_workspace_for_user(db, telegram_id, category.workspace_id, require_write=True)
    if category.workspace_id != workspace.id:
        raise ValueError("category_not_in_workspace")

    if name is not None and name != category.name:
        existing = _get_category_by_name(db, workspace.id, name, category.type)
        if existing and existing.id != category.id:
            raise ValueError("category_name_conflict")
        category.name = name
    if emoji is not None:
        category.emoji = emoji
    if is_archived is not None:
        category.is_archived = is_archived
    db.commit()
    db.refresh(category)
    return category


def get_or_create_category(
    db: Session,
    workspace_id: int,
    created_by_user_id: int,
    name: str,
    category_type: models.OperationType,
) -> models.Category:
    """Возвращает данные для сценария «or create category»."""
    existing = _get_category_by_name(db, workspace_id, name, category_type)
    if existing:
        return existing

    category = models.Category(
        workspace_id=workspace_id,
        created_by_user_id=created_by_user_id,
        name=name,
        type=category_type,
    )
    db.add(category)
    db.flush()
    return category


def _get_category_or_raise(db: Session, category_id: int) -> models.Category:
    """Выполняет действие «get category or raise» в рамках логики Finance Helper."""
    category = db.get(models.Category, category_id)
    if not category:
        raise ValueError("category_not_found")
    return category


def create_alias(db: Session, telegram_id: int, category_id: int, alias: str) -> models.CategoryAlias:
    """Создаёт сущность для сценария «alias»."""
    _, workspace, _ = resolve_workspace_for_user(
        db,
        telegram_id,
        _get_category_or_raise(db, category_id).workspace_id,
        require_write=True,
    )
    category = _get_category_or_raise(db, category_id)
    if category.workspace_id != workspace.id:
        raise ValueError("category_not_in_workspace")

    normalized = _normalize_alias(alias)
    existing = db.scalar(
        select(models.CategoryAlias).where(
            models.CategoryAlias.workspace_id == workspace.id,
            models.CategoryAlias.normalized_alias == normalized,
        )
    )
    if existing:
        raise ValueError("alias_conflict")

    obj = models.CategoryAlias(
        workspace_id=workspace.id,
        category_id=category.id,
        alias=alias,
        normalized_alias=normalized,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_aliases(db: Session, telegram_id: int, category_id: int) -> list[models.CategoryAlias]:
    """Возвращает список сущностей для сценария «aliases»."""
    category = _get_category_or_raise(db, category_id)
    resolve_workspace_for_user(db, telegram_id, category.workspace_id)
    stmt = select(models.CategoryAlias).where(models.CategoryAlias.category_id == category_id).order_by(models.CategoryAlias.alias.asc())
    return db.scalars(stmt).all()


def delete_alias(db: Session, telegram_id: int, alias_id: int) -> bool:
    """Удаляет сущность в сценарии «alias»."""
    alias = db.get(models.CategoryAlias, alias_id)
    if not alias:
        return False
    resolve_workspace_for_user(db, telegram_id, alias.workspace_id, require_write=True)
    res = db.execute(delete(models.CategoryAlias).where(models.CategoryAlias.id == alias_id))
    db.commit()
    return bool(res.rowcount)


def match_category(
    db: Session,
    telegram_id: int,
    workspace_id: int | None,
    text: str,
    category_type: models.OperationType,
) -> models.Category | None:
    """Выполняет действие «match category» в рамках логики Finance Helper."""
    _, workspace, _ = resolve_workspace_for_user(db, telegram_id, workspace_id)
    normalized = _normalize_alias(text)

    alias_rows = db.execute(
        select(models.CategoryAlias, models.Category)
        .join(models.Category, models.Category.id == models.CategoryAlias.category_id)
        .where(
            models.CategoryAlias.workspace_id == workspace.id,
            models.Category.type == category_type,
            models.Category.is_archived.is_(False),
        )
    ).all()

    best_category = None
    best_len = 0
    for alias, category in alias_rows:
        if alias.normalized_alias and alias.normalized_alias in normalized and len(alias.normalized_alias) > best_len:
            best_category = category
            best_len = len(alias.normalized_alias)
    if best_category:
        return best_category

    category_rows = db.scalars(
        select(models.Category).where(
            models.Category.workspace_id == workspace.id,
            models.Category.type == category_type,
            models.Category.is_archived.is_(False),
        )
    ).all()
    normalized_words = f" {normalized} "
    for category in category_rows:
        name_norm = _normalize_alias(category.name)
        if f" {name_norm} " in normalized_words:
            return category
    return None


# ---------- limits / reports / uploads ----------


def set_daily_limit(db: Session, telegram_id: int, daily_limit: float) -> models.User:
    """Выполняет действие «set daily limit» в рамках логики Finance Helper."""
    user = _get_user_or_raise(db, telegram_id)
    workspace = _ensure_personal_workspace(db, user)
    user.daily_limit = daily_limit

    existing = db.scalar(
        select(models.BudgetLimit).where(
            models.BudgetLimit.workspace_id == workspace.id,
            models.BudgetLimit.user_id == user.id,
            models.BudgetLimit.scope == models.LimitScope.user,
            models.BudgetLimit.period == models.LimitPeriod.daily,
        )
    )
    if existing:
        existing.amount = daily_limit
        existing.currency = user.base_currency
        existing.is_active = True
    else:
        db.add(
            models.BudgetLimit(
                workspace_id=workspace.id,
                user_id=user.id,
                scope=models.LimitScope.user,
                period=models.LimitPeriod.daily,
                amount=daily_limit,
                currency=user.base_currency,
            )
        )

    db.commit()
    db.refresh(user)
    return user


def create_or_update_budget_limit(
    db: Session,
    telegram_id: int,
    workspace_id: int | None,
    scope: models.LimitScope,
    period: models.LimitPeriod,
    amount: float,
    currency: str,
    user_telegram_id: int | None,
    category_id: int | None,
    notify_at_50: bool,
    notify_at_80: bool,
    notify_at_100: bool,
) -> models.BudgetLimit:
    """Создаёт сущность для сценария «or update budget limit»."""
    _, workspace, _ = resolve_workspace_for_user(db, telegram_id, workspace_id, require_write=True)

    target_user_id: int | None = None
    if user_telegram_id is not None:
        target_user_id = _get_user_or_raise(db, user_telegram_id).id
        if not _membership_for_user(db, workspace.id, target_user_id):
            raise ValueError("target_user_not_in_workspace")

    if category_id is not None:
        category = _get_category_or_raise(db, category_id)
        if category.workspace_id != workspace.id:
            raise ValueError("category_not_in_workspace")

    stmt = select(models.BudgetLimit).where(
        models.BudgetLimit.workspace_id == workspace.id,
        models.BudgetLimit.scope == scope,
        models.BudgetLimit.period == period,
    )
    stmt = stmt.where(models.BudgetLimit.user_id == target_user_id) if target_user_id is not None else stmt.where(models.BudgetLimit.user_id.is_(None))
    stmt = stmt.where(models.BudgetLimit.category_id == category_id) if category_id is not None else stmt.where(models.BudgetLimit.category_id.is_(None))
    existing = db.scalar(stmt)

    if existing:
        existing.amount = amount
        existing.currency = currency.upper()
        existing.notify_at_50 = notify_at_50
        existing.notify_at_80 = notify_at_80
        existing.notify_at_100 = notify_at_100
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return existing

    limit = models.BudgetLimit(
        workspace_id=workspace.id,
        user_id=target_user_id,
        category_id=category_id,
        scope=scope,
        period=period,
        amount=amount,
        currency=currency.upper(),
        notify_at_50=notify_at_50,
        notify_at_80=notify_at_80,
        notify_at_100=notify_at_100,
    )
    db.add(limit)
    db.commit()
    db.refresh(limit)
    return limit


def list_budget_limits(db: Session, telegram_id: int, workspace_id: int | None) -> list[models.BudgetLimit]:
    """Возвращает список сущностей для сценария «budget limits»."""
    _, workspace, _ = resolve_workspace_for_user(db, telegram_id, workspace_id)
    stmt = (
        select(models.BudgetLimit)
        .where(models.BudgetLimit.workspace_id == workspace.id, models.BudgetLimit.is_active.is_(True))
        .order_by(models.BudgetLimit.period.asc(), models.BudgetLimit.scope.asc(), models.BudgetLimit.id.asc())
    )
    return db.scalars(stmt).all()


def upsert_report_schedule(
    db: Session,
    telegram_id: int,
    workspace_id: int | None,
    user_telegram_id: int | None,
    frequency: str,
    day_of_month: int,
    send_time: str,
    timezone: str,
    enabled: bool,
) -> models.ReportSchedule:
    """Выполняет действие «upsert report schedule» в рамках логики Finance Helper."""
    _, workspace, _ = resolve_workspace_for_user(db, telegram_id, workspace_id, require_write=True)

    target_user_id = None
    if user_telegram_id is not None:
        target_user_id = _get_user_or_raise(db, user_telegram_id).id

    stmt = select(models.ReportSchedule).where(
        models.ReportSchedule.workspace_id == workspace.id,
        models.ReportSchedule.frequency == frequency,
    )
    stmt = stmt.where(models.ReportSchedule.user_id == target_user_id) if target_user_id is not None else stmt.where(models.ReportSchedule.user_id.is_(None))
    existing = db.scalar(stmt)

    if existing:
        existing.day_of_month = day_of_month
        existing.send_time = send_time
        existing.timezone = timezone
        existing.enabled = enabled
        db.commit()
        db.refresh(existing)
        return existing

    schedule = models.ReportSchedule(
        workspace_id=workspace.id,
        user_id=target_user_id,
        frequency=frequency,
        day_of_month=day_of_month,
        send_time=send_time,
        timezone=timezone,
        enabled=enabled,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def list_report_schedules(db: Session, telegram_id: int, workspace_id: int | None) -> list[models.ReportSchedule]:
    """Возвращает список сущностей для сценария «report schedules»."""
    _, workspace, _ = resolve_workspace_for_user(db, telegram_id, workspace_id)
    stmt = select(models.ReportSchedule).where(models.ReportSchedule.workspace_id == workspace.id).order_by(models.ReportSchedule.id.asc())
    return db.scalars(stmt).all()


def create_receipt_upload(
    db: Session,
    telegram_id: int,
    workspace_id: int | None,
    original_filename: str | None,
    telegram_file_id: str | None,
    storage_path: str | None,
) -> models.ReceiptUpload:
    """Создаёт сущность для сценария «receipt upload»."""
    user, workspace, _ = resolve_workspace_for_user(db, telegram_id, workspace_id, require_write=True)
    obj = models.ReceiptUpload(
        workspace_id=workspace.id,
        uploaded_by_user_id=user.id,
        original_filename=original_filename,
        telegram_file_id=telegram_file_id,
        storage_path=storage_path,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_statement_import(
    db: Session,
    telegram_id: int,
    workspace_id: int | None,
    original_filename: str | None,
    file_type: str | None,
    summary_text: str | None,
) -> models.StatementImport:
    """Создаёт сущность для сценария «statement import»."""
    user, workspace, _ = resolve_workspace_for_user(db, telegram_id, workspace_id, require_write=True)
    obj = models.StatementImport(
        workspace_id=workspace.id,
        uploaded_by_user_id=user.id,
        original_filename=original_filename,
        file_type=file_type,
        summary_text=summary_text,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_receipt_upload(db: Session, telegram_id: int, receipt_id: int) -> models.ReceiptUpload:
    """Возвращает данные для сценария «receipt upload»."""
    user = _get_user_or_raise(db, telegram_id)
    obj = db.scalar(select(models.ReceiptUpload).where(models.ReceiptUpload.id == receipt_id))
    if not obj:
        raise ValueError("receipt_not_found")
    membership = _membership_for_user(db, obj.workspace_id, user.id)
    if not membership:
        raise ValueError("workspace_access_denied")
    return obj


def update_receipt_upload(
    db: Session,
    telegram_id: int,
    receipt_id: int,
    parsed_total: float | None,
    parsed_currency: str | None,
    parsed_merchant: str | None,
    parsed_date: date | None,
    raw_text: str | None,
    error_message: str | None,
    status: models.ImportStatus,
) -> models.ReceiptUpload:
    """Обновляет данные в сценарии «receipt upload»."""
    obj = get_receipt_upload(db, telegram_id, receipt_id)
    requester = _get_user_or_raise(db, telegram_id)
    membership = _membership_for_user(db, obj.workspace_id, requester.id)
    if membership.role == models.MemberRole.viewer:
        raise ValueError("workspace_readonly")
    obj.parsed_total = parsed_total
    obj.parsed_currency = parsed_currency.upper() if parsed_currency else None
    obj.parsed_merchant = parsed_merchant
    obj.parsed_date = parsed_date
    obj.raw_text = raw_text
    obj.error_message = error_message
    obj.status = status
    db.commit()
    db.refresh(obj)
    return obj


def finalize_statement_import(
    db: Session,
    telegram_id: int,
    import_id: int,
    imported_rows: int,
    skipped_rows: int,
    summary_text: str | None,
    error_message: str | None,
    status: models.ImportStatus,
) -> models.StatementImport:
    """Выполняет действие «finalize statement import» в рамках логики Finance Helper."""
    user = _get_user_or_raise(db, telegram_id)
    obj = db.scalar(select(models.StatementImport).where(models.StatementImport.id == import_id))
    if not obj:
        raise ValueError("statement_import_not_found")
    membership = _membership_for_user(db, obj.workspace_id, user.id)
    if not membership:
        raise ValueError("workspace_access_denied")
    if membership.role == models.MemberRole.viewer:
        raise ValueError("workspace_readonly")
    obj.imported_rows = imported_rows
    obj.skipped_rows = skipped_rows
    obj.summary_text = summary_text
    obj.error_message = error_message
    obj.status = status
    db.commit()
    db.refresh(obj)
    return obj


# ---------- operations ----------


def create_operation(
    db: Session,
    telegram_id: int,
    workspace_id: int | None,
    op_type: str,
    amount: float,
    currency: str,
    category: str | None,
    comment: str | None,
    source: str | None,
    occurred_at: date | None,
    user_telegram_id: int | None,
    actor_telegram_id: int | None,
    merchant: str | None = None,
    external_ref: str | None = None,
    is_imported: bool = False,
    receipt_upload_id: int | None = None,
    statement_import_id: int | None = None,
) -> models.Operation:
    """Создаёт сущность для сценария «operation»."""
    requester, workspace, _ = resolve_workspace_for_user(db, telegram_id, workspace_id, require_write=True)

    subject_user = requester if user_telegram_id is None else _get_user_or_raise(db, user_telegram_id)
    actor_user = requester if actor_telegram_id is None else _get_user_or_raise(db, actor_telegram_id)

    if not _membership_for_user(db, workspace.id, subject_user.id):
        raise ValueError("target_user_not_in_workspace")
    if not _membership_for_user(db, workspace.id, actor_user.id):
        raise ValueError("actor_user_not_in_workspace")

    category_id = None
    if category:
        cat = get_or_create_category(db, workspace.id, requester.id, category, models.OperationType(op_type))
        category_id = cat.id

    if external_ref:
        existing = db.scalar(
            select(models.Operation).where(
                models.Operation.workspace_id == workspace.id,
                models.Operation.external_ref == external_ref,
            )
        )
        if existing:
            return existing

    op = models.Operation(
        workspace_id=workspace.id,
        user_id=subject_user.id,
        created_by_user_id=actor_user.id,
        type=models.OperationType(op_type),
        amount=amount,
        currency=currency.upper(),
        category_id=category_id,
        comment=comment,
        source=source,
        merchant=merchant,
        external_ref=external_ref,
        is_imported=is_imported,
        receipt_upload_id=receipt_upload_id,
        statement_import_id=statement_import_id,
        occurred_at=occurred_at or date.today(),
    )
    db.add(op)
    db.commit()
    db.refresh(op)
    return op


def confirm_receipt_upload(
    db: Session,
    telegram_id: int,
    receipt_id: int,
    category: str | None,
    comment: str | None,
    currency: str | None,
    amount: float | None,
    occurred_at: date | None,
) -> models.Operation:
    """Выполняет действие «confirm receipt upload» в рамках логики Finance Helper."""
    receipt = get_receipt_upload(db, telegram_id, receipt_id)
    final_amount = float(amount if amount is not None else (receipt.parsed_total or 0))
    if final_amount <= 0:
        raise ValueError("receipt_amount_missing")
    final_currency = (currency or receipt.parsed_currency or "RUB").upper()
    final_comment = comment or receipt.parsed_merchant or receipt.original_filename or "Чек"
    op = create_operation(
        db=db,
        telegram_id=telegram_id,
        workspace_id=receipt.workspace_id,
        op_type="expense",
        amount=final_amount,
        currency=final_currency,
        category=category,
        comment=final_comment,
        source="receipt_ocr",
        occurred_at=occurred_at or receipt.parsed_date,
        user_telegram_id=None,
        actor_telegram_id=None,
        merchant=receipt.parsed_merchant,
        receipt_upload_id=receipt.id,
    )
    receipt.status = models.ImportStatus.confirmed
    receipt.confirmed_at = func.now()
    db.commit()
    db.refresh(op)
    return op


def list_operations(
    db: Session,
    telegram_id: int,
    workspace_id: int | None,
    limit: int = 10,
    offset: int = 0,
    date_from: date | None = None,
    date_to: date | None = None,
    op_type: str | None = None,
    category_id: int | None = None,
    category_name: str | None = None,
    user_telegram_id: int | None = None,
    actor_telegram_id: int | None = None,
    search: str | None = None,
):
    """Возвращает список сущностей для сценария «operations»."""
    _, workspace, _ = resolve_workspace_for_user(db, telegram_id, workspace_id)

    subject_user = aliased(models.User)
    actor_user = aliased(models.User)
    stmt = (
        select(models.Operation, models.Category.name, subject_user.telegram_id, actor_user.telegram_id)
        .join(models.Category, models.Operation.category_id == models.Category.id, isouter=True)
        .join(subject_user, models.Operation.user_id == subject_user.id)
        .join(actor_user, models.Operation.created_by_user_id == actor_user.id)
        .where(models.Operation.workspace_id == workspace.id)
    )

    if date_from:
        stmt = stmt.where(models.Operation.occurred_at >= date_from)
    if date_to:
        stmt = stmt.where(models.Operation.occurred_at <= date_to)
    if op_type:
        stmt = stmt.where(models.Operation.type == models.OperationType(op_type))
    if category_id is not None:
        stmt = stmt.where(models.Operation.category_id == category_id)
    if category_name:
        stmt = stmt.where(models.Category.name == category_name)
    if user_telegram_id is not None:
        stmt = stmt.where(subject_user.telegram_id == user_telegram_id)
    if actor_telegram_id is not None:
        stmt = stmt.where(actor_user.telegram_id == actor_telegram_id)
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                models.Operation.comment.ilike(pattern),
                models.Operation.source.ilike(pattern),
                models.Operation.merchant.ilike(pattern),
                models.Category.name.ilike(pattern),
            )
        )

    stmt = stmt.order_by(models.Operation.occurred_at.desc(), models.Operation.id.desc()).limit(limit).offset(offset)
    return db.execute(stmt).all()


def update_operation(
    db: Session,
    telegram_id: int,
    op_id: int,
    amount: float | None,
    currency: str | None,
    comment: str | None,
    category: str | None,
    occurred_at: date | None,
) -> models.Operation:
    """Обновляет данные в сценарии «operation»."""
    requester = _get_user_or_raise(db, telegram_id)
    op = db.scalar(select(models.Operation).where(models.Operation.id == op_id))
    if not op:
        raise ValueError("op_not_found")

    membership = _membership_for_user(db, op.workspace_id, requester.id)
    if not membership:
        raise ValueError("workspace_access_denied")
    if membership.role == models.MemberRole.viewer:
        raise ValueError("workspace_readonly")

    if amount is not None:
        op.amount = amount
    if currency is not None:
        op.currency = currency.upper()
    if comment is not None:
        op.comment = comment
    if occurred_at is not None:
        op.occurred_at = occurred_at
    if category is not None:
        cat = get_or_create_category(db, op.workspace_id, requester.id, category, op.type)
        op.category_id = cat.id

    db.commit()
    db.refresh(op)
    return op


def delete_operation(db: Session, telegram_id: int, op_id: int) -> bool:
    """Удаляет сущность в сценарии «operation»."""
    requester = _get_user_or_raise(db, telegram_id)
    op = db.scalar(select(models.Operation).where(models.Operation.id == op_id))
    if not op:
        return False

    membership = _membership_for_user(db, op.workspace_id, requester.id)
    if not membership:
        raise ValueError("workspace_access_denied")
    if membership.role == models.MemberRole.viewer:
        raise ValueError("workspace_readonly")

    res = db.execute(delete(models.Operation).where(models.Operation.id == op_id))
    db.commit()
    return bool(res.rowcount)


def daily_expense_total(db: Session, telegram_id: int, day: date, workspace_id: int | None = None) -> tuple[float, models.User]:
    """Выполняет действие «daily expense total» в рамках логики Finance Helper."""
    user, workspace, _ = resolve_workspace_for_user(db, telegram_id, workspace_id)
    total = db.scalar(
        select(func.coalesce(func.sum(models.Operation.amount), 0)).where(
            models.Operation.workspace_id == workspace.id,
            models.Operation.user_id == user.id,
            models.Operation.type == models.OperationType.expense,
            models.Operation.occurred_at == day,
        )
    )
    return float(total or 0), user


# ---------- stage 6/7 helpers ----------


def _period_bounds(period: models.LimitPeriod, day: date) -> tuple[date, date]:
    """Выполняет действие «period bounds» в рамках логики Finance Helper."""
    if period == models.LimitPeriod.daily:
        return day, day
    month_start = day.replace(day=1)
    if day.month == 12:
        next_month = day.replace(year=day.year + 1, month=1, day=1)
    else:
        next_month = day.replace(month=day.month + 1, day=1)
    month_end = next_month - timedelta(days=1)
    return month_start, month_end


def _limit_label(db: Session, limit: models.BudgetLimit) -> str:
    """Выполняет действие «limit label» в рамках логики Finance Helper."""
    parts: list[str] = []
    if limit.scope == models.LimitScope.workspace:
        parts.append('общий бюджет')
    elif limit.scope == models.LimitScope.user:
        if limit.user_id:
            user = db.get(models.User, limit.user_id)
            parts.append(f"бюджет пользователя {user.username or user.telegram_id}")
        else:
            parts.append('личный бюджет')
    elif limit.scope == models.LimitScope.category:
        cat = db.get(models.Category, limit.category_id) if limit.category_id else None
        parts.append(f"категория «{cat.name if cat else 'Без категории'}»")
    parts.append('в день' if limit.period == models.LimitPeriod.daily else 'в месяц')
    return ' '.join(parts)


def _expense_total_for_limit(
    db: Session,
    workspace_id: int,
    limit: models.BudgetLimit,
    day: date,
) -> float:
    """Выполняет действие «expense total for limit» в рамках логики Finance Helper."""
    date_from, date_to = _period_bounds(limit.period, day)
    stmt = select(func.coalesce(func.sum(models.Operation.amount), 0)).where(
        models.Operation.workspace_id == workspace_id,
        models.Operation.type == models.OperationType.expense,
        models.Operation.occurred_at >= date_from,
        models.Operation.occurred_at <= date_to,
    )
    if limit.scope == models.LimitScope.user and limit.user_id is not None:
        stmt = stmt.where(models.Operation.user_id == limit.user_id)
    if limit.scope == models.LimitScope.category and limit.category_id is not None:
        stmt = stmt.where(models.Operation.category_id == limit.category_id)
    return float(db.scalar(stmt) or 0)


def get_budget_limits_overview(
    db: Session,
    telegram_id: int,
    workspace_id: int | None,
    day: date | None = None,
) -> list[dict]:
    """Возвращает данные для сценария «budget limits overview»."""
    _, workspace, _ = resolve_workspace_for_user(db, telegram_id, workspace_id)
    ref_day = day or date.today()
    rows = list_budget_limits(db, telegram_id, workspace_id)
    result: list[dict] = []
    for limit in rows:
        spent = _expense_total_for_limit(db, workspace.id, limit, ref_day)
        amount = float(limit.amount)
        remaining = round(amount - spent, 2)
        percent = round((spent / amount) * 100, 1, ) if amount > 0 else 0.0
        cat = db.get(models.Category, limit.category_id) if limit.category_id else None
        user = db.get(models.User, limit.user_id) if limit.user_id else None
        result.append({
            'id': limit.id,
            'workspace_id': limit.workspace_id,
            'scope': limit.scope,
            'period': limit.period,
            'amount': amount,
            'currency': limit.currency,
            'spent': round(spent, 2),
            'remaining': round(remaining, 2),
            'percent_used': max(round(percent, 1), 0.0),
            'user_telegram_id': user.telegram_id if user else None,
            'category_id': limit.category_id,
            'category_name': cat.name if cat else None,
            'label': _limit_label(db, limit),
            'is_active': limit.is_active,
        })
    return result


def evaluate_limit_alerts_for_operation(db: Session, op: models.Operation) -> list[dict]:
    """Выполняет действие «evaluate limit alerts for operation» в рамках логики Finance Helper."""
    if op.type != models.OperationType.expense:
        return []
    stmt = select(models.BudgetLimit).where(
        models.BudgetLimit.workspace_id == op.workspace_id,
        models.BudgetLimit.is_active.is_(True),
    )
    candidates = db.scalars(stmt).all()
    alerts: list[dict] = []
    amount = float(op.amount)
    for limit in candidates:
        if limit.scope == models.LimitScope.user and limit.user_id != op.user_id:
            continue
        if limit.scope == models.LimitScope.category and limit.category_id != op.category_id:
            continue
        spent_after = _expense_total_for_limit(db, op.workspace_id, limit, op.occurred_at)
        spent_before = max(spent_after - amount, 0.0)
        thresholds = [
            (50, 0.5, bool(limit.notify_at_50)),
            (80, 0.8, bool(limit.notify_at_80)),
            (100, 1.0, bool(limit.notify_at_100)),
        ]
        limit_amount = float(limit.amount)
        if limit_amount <= 0:
            continue
        for threshold_value, threshold_ratio, enabled in thresholds:
            if not enabled:
                continue
            if (spent_before / limit_amount) < threshold_ratio <= (spent_after / limit_amount):
                alerts.append({
                    'limit_id': limit.id,
                    'scope': limit.scope,
                    'period': limit.period,
                    'threshold': threshold_value,
                    'amount': limit_amount,
                    'spent': round(spent_after, 2),
                    'remaining': round(limit_amount - spent_after, 2),
                    'currency': limit.currency,
                    'label': _limit_label(db, limit),
                })
    alerts.sort(key=lambda item: (item['threshold'], item['limit_id']))
    return alerts


def list_due_report_schedules(db: Session, run_date: date, send_time: str, frequency: str = 'monthly') -> list[dict]:
    """Возвращает список сущностей для сценария «due report schedules»."""
    stmt = select(models.ReportSchedule).where(
        models.ReportSchedule.enabled.is_(True),
        models.ReportSchedule.frequency == frequency,
        models.ReportSchedule.day_of_month == run_date.day,
        models.ReportSchedule.send_time == send_time,
    )
    schedules = db.scalars(stmt).all()
    result: list[dict] = []
    for item in schedules:
        target_user = db.get(models.User, item.user_id) if item.user_id else None
        workspace = db.get(models.Workspace, item.workspace_id)
        owner = db.get(models.User, workspace.owner_user_id) if workspace else None
        telegram_id = target_user.telegram_id if target_user else (owner.telegram_id if owner else None)
        if telegram_id is None:
            continue
        result.append({
            'id': item.id,
            'workspace_id': item.workspace_id,
            'telegram_id': telegram_id,
            'frequency': item.frequency,
            'day_of_month': item.day_of_month,
            'send_time': item.send_time,
            'timezone': item.timezone,
            'enabled': item.enabled,
        })
    return result
