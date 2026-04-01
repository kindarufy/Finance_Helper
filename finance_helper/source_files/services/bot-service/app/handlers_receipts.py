"""Обработчики Telegram-бота для загрузки чеков и импорта банковских выписок."""
from pathlib import Path

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup

from . import api
from .bot import dp
from .common import fmt_money
from .helpers import _current_workspace_id
from .keyboards import MENU_KB
from .states import StatementImportFlow
from .utils import infer_default_category, parse_statement_file
from .config import settings
from .navigation import try_interrupt_current_flow


async def _download_telegram_file(message: Message, file_id: str, target_path: Path) -> None:
    """Скачивает файл из Telegram во временное хранилище."""
    tg_file = await message.bot.get_file(file_id)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("wb") as output:
        await message.bot.download(tg_file, destination=output)


async def _resolve_category_from_text(telegram_id: int, raw_text: str | None, op_type: str) -> str | None:
    """Пытается подобрать категорию по тексту импортируемой операции."""
    if not raw_text:
        return None
    try:
        workspace_id = await _current_workspace_id(telegram_id)
        matched = await api.match_category(telegram_id, raw_text, op_type, workspace_id=workspace_id)
        if matched.get("matched") and matched.get("category"):
            return matched["category"].get("name")
    except Exception:
        pass
    return infer_default_category(raw_text, op_type)


@dp.message(F.text == "🏦 Импорт")
async def menu_statement_import(message: Message, state: FSMContext):
    """Открывает раздел импорта банковской выписки."""
    await state.set_state(StatementImportFlow.waiting_file)
    await message.answer(
        "Отправь банковскую выписку в CSV или XLSX.\nЯ разберу файл, покажу сколько операций нашла, и предложу импортировать их в бюджет.",
        reply_markup=MENU_KB,
    )


@dp.message(StatementImportFlow.waiting_file, F.document)
async def handle_statement_file(message: Message, state: FSMContext):
    """Обрабатывает загруженный файл выписки и подготавливает предварительный импорт."""
    document = message.document
    if not document or not document.file_name:
        await message.answer("Пришли документ CSV или XLSX.", reply_markup=MENU_KB)
        return
    suffix = Path(document.file_name).suffix.lower()
    if suffix not in {".csv", ".xlsx", ".xlsm", ".xltx", ".xltm"}:
        await message.answer("Поддерживаются только CSV и XLSX файлы.", reply_markup=MENU_KB)
        return
    file_path = Path(settings.upload_dir) / "statements" / f"{message.from_user.id}_{message.message_id}{suffix}"
    await _download_telegram_file(message, document.file_id, file_path)
    content = file_path.read_bytes()
    try:
        rows, summary = parse_statement_file(document.file_name, content)
    except Exception as exc:
        await message.answer(f"Не получилось разобрать выписку: {exc}", reply_markup=MENU_KB)
        await state.clear()
        return
    record = await api.create_statement_import_record(
        telegram_id=message.from_user.id,
        original_filename=document.file_name,
        file_type=summary.get("file_type"),
        summary_text=summary.get("message"),
        workspace_id=await _current_workspace_id(message.from_user.id),
    )
    await state.update_data(statement_payload={"import_id": record["id"], "rows": rows, "summary": summary, "filename": document.file_name})
    await state.set_state(StatementImportFlow.confirm)
    preview_lines = []
    merchant_labels: list[str] = []
    for row in rows[:5]:
        merchant = row.get("merchant") or row.get("comment") or "—"
        merchant_labels.append(str(merchant))
        preview_lines.append(f"• {row['occurred_at']} — {fmt_money(row['amount'])} {row['currency']} — {merchant}")
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Импортировать", callback_data="stmt:confirm"), InlineKeyboardButton(text="❌ Отмена", callback_data="stmt:cancel")]])
    await message.answer(
        f"🏦 Выписка разобрана\n\nФайл: {document.file_name}\n"
        f"Найдено операций: {summary.get('rows', 0)}\n"
        f"Расходов: {summary.get('expenses', 0)} на {fmt_money(summary.get('total_expense', 0))}\n"
        f"Доходов: {summary.get('incomes', 0)} на {fmt_money(summary.get('total_income', 0))}\n\n"
        f"Первые операции:\n" + ("\n".join(preview_lines) if preview_lines else "—"),
        reply_markup=kb,
    )




@dp.message(StatementImportFlow.waiting_file)
async def statement_waiting_text(message: Message, state: FSMContext):
    """Обрабатывает ввод пользователя на шаге ожидания файла банковской выписки."""
    if await try_interrupt_current_flow(message, state):
        return

    await message.answer(
        "Сейчас я жду CSV или XLSX файл. Можно отправить файл или выбрать другой раздел в меню.",
        reply_markup=MENU_KB,
    )


@dp.callback_query(F.data == "stmt:confirm")
async def cb_statement_confirm(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает callback для подтверждения импорта выписки."""
    data = await state.get_data()
    payload = data.get("statement_payload") or {}
    rows = payload.get("rows") or []
    imported = 0
    skipped = 0
    workspace_id = await _current_workspace_id(callback.from_user.id)
    for row in rows:
        category = await _resolve_category_from_text(callback.from_user.id, row.get("comment") or row.get("merchant"), row["type"])
        if not category and row["type"] == "expense":
            category = "Другое"
        try:
            await api.create_operation(
                telegram_id=callback.from_user.id,
                workspace_id=workspace_id,
                op_type=row["type"],
                amount=float(row["amount"]),
                category=category,
                comment=row.get("comment"),
                source="statement_import",
                occurred_at=row.get("occurred_at"),
                currency=row.get("currency") or "RUB",
                merchant=row.get("merchant"),
                external_ref=row.get("external_ref"),
                is_imported=True,
                statement_import_id=int(payload["import_id"]),
            )
            imported += 1
        except Exception:
            skipped += 1
    summary_text = f"Импортировано: {imported}. Пропущено: {skipped}."
    try:
        await api.complete_statement_import(
            import_id=int(payload["import_id"]),
            telegram_id=callback.from_user.id,
            imported_rows=imported,
            skipped_rows=skipped,
            summary_text=summary_text,
            status="confirmed",
        )
    except Exception:
        pass
    await callback.message.edit_text(f"✅ Импорт выписки завершён.\n{summary_text}")
    await callback.message.answer("Готово 👌", reply_markup=MENU_KB)
    await state.clear()
    await callback.answer()




@dp.message(StatementImportFlow.confirm)
async def statement_confirm_text(message: Message, state: FSMContext):
    """Обрабатывает ввод пользователя на шаге подтверждения импорта банковской выписки."""
    if await try_interrupt_current_flow(message, state):
        return

    await message.answer(
        "Импорт уже разобран. Нажми inline-кнопку «Импортировать» или «Отмена», либо выбери другой раздел в меню.",
        reply_markup=MENU_KB,
    )


@dp.callback_query(F.data == "stmt:cancel")
async def cb_statement_cancel(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает callback для отмены импорта выписки."""
    data = await state.get_data()
    payload = data.get("statement_payload") or {}
    if payload.get("import_id"):
        try:
            await api.complete_statement_import(
                import_id=int(payload["import_id"]),
                telegram_id=callback.from_user.id,
                imported_rows=0,
                skipped_rows=0,
                summary_text="Импорт отменён пользователем",
                status="failed",
            )
        except Exception:
            pass
    await state.clear()
    await callback.message.edit_text("Ок, импорт выписки отменён ✅")
    await callback.answer()


