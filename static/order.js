const form = document.querySelector("#order-form");
const submitButton = document.querySelector("#order-submit");
const message = document.querySelector("#order-message");

const moneyFormatter = new Intl.NumberFormat("uk-UA", {
    style: "currency",
    currency: "UAH",
});

let submissionLocked = false;

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (submissionLocked || !form.reportValidity()) {
        return;
    }

    submissionLocked = true;
    submitButton.disabled = true;
    message.textContent = "Надсилаємо заявку…";

    const fields = new FormData(form);

    const payload = {
        customer_name: fields.get("customer_name").trim(),
        customer_phone: fields.get("customer_phone").trim(),
        requested_date: fields.get("requested_date"),
        customer_note: fields.get("customer_note").trim() || null,
        items: [
            {
                cake_id: Number(form.dataset.cakeId),
                quantity: Number(fields.get("quantity")),
            },
        ],
    };

    try {
        const response = await fetch(form.action, {
            method: "POST",
            credentials: "omit",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        // These responses mean the API rejected the submitted order.
        if (response.status === 400 || response.status === 422) {
            message.textContent =
                response.status === 400
                    ? "Цей торт більше недоступний. Оновіть сторінку каталогу."
                    : "Перевірте ім’я, телефон, кількість і дату. Дата має бути після сьогодні.";

            submissionLocked = false;
            submitButton.disabled = false;
            return;
        }

        if (response.status !== 201) {
            throw new Error("Unexpected response");
        }

        const order = await response.json();
        const total = moneyFormatter.format(order.total_kopiyky / 100);

        form.hidden = true;
        message.textContent =
            `Заявку №${order.id} отримано. Сума: ${total}. ` +
            "Дата та деталі очікують підтвердження. Оплату ще не здійснено.";
    } catch {
        message.textContent =
            "Не вдалося отримати підтвердження. Заявка могла зберегтися. " +
            "Перед повторним надсиланням уточніть у продавця, чи її отримано.";
    }
});

submitButton.disabled = false;