import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
    FaArrowLeft,
    FaTrash,
    FaPlusCircle,
} from "react-icons/fa";

const AddPhonePage: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const barrierId = location.state?.barrier_id;
    const accessToken = location.state?.access_token;

    const [phone, setPhone] = useState("+7");
    const [name, setName] = useState("");
    const [type, setType] = useState<"common" | "temporary" | "schedule">("common");

    const [startTime, setStartTime] = useState("");
    const [endTime, setEndTime] = useState("");

    const [schedule, setSchedule] = useState<any>({
        monday: [],
        tuesday: [],
        wednesday: [],
        thursday: [],
        friday: [],
        saturday: [],
        sunday: [],
    });

    const [error, setError] = useState("");

    const handleSave = async () => {
        setError("");

        if (!phone || !name) {
            setError("Введите имя и номер телефона.");
            return;
        }

        const payload: any = {
            phone,
            name,
            type,
        };

        if (type === "temporary") {
            if (!startTime || !endTime) {
                setError("Укажите время начала и конца.");
                return;
            }
            if (new Date(startTime) >= new Date(endTime)) {
                setError("Время начала должно быть раньше времени конца.");
                return;
            }

            payload.start_time = startTime;
            payload.end_time = endTime;
        }

        if (type === "schedule") {
            payload.schedule = schedule;
        }

        try {
            const res = await fetch(`/api/barriers/${barrierId}/phones/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${accessToken}`,
                },
                body: JSON.stringify(payload),
            });

            if (res.ok) {
                navigate("/mybarrier", {
                    state: { barrier_id: barrierId, access_token: accessToken },
                });
            } else {
                const data = await res.json();
                setError(data.detail || "Ошибка при сохранении номера.");
            }
        } catch (e) {
            setError("Ошибка сети.");
        }
    };

    const addSchedulePeriod = (day: string) => {
        const updated = { ...schedule };
        updated[day].push({ start_time: "08:00", end_time: "12:00" });
        setSchedule(updated);
    };

    const renderScheduleEditor = () => {
        return (
            <>
                {Object.keys(schedule).map((day) => (
                    <div key={day} style={{ marginBottom: "10px" }}>
                        <strong>{day.charAt(0).toUpperCase() + day.slice(1)}:</strong>
                        {schedule[day].map((period: any, i: number) => (
                            <div key={i} style={{ display: "flex", gap: "10px", marginTop: "5px" }}>
                                <input
                                    type="time"
                                    value={period.start_time}
                                    onChange={(e) => {
                                        const updated = [...schedule[day]];
                                        updated[i].start_time = e.target.value;
                                        setSchedule({ ...schedule, [day]: updated });
                                    }}
                                />
                                <input
                                    type="time"
                                    value={period.end_time}
                                    onChange={(e) => {
                                        const updated = [...schedule[day]];
                                        updated[i].end_time = e.target.value;
                                        setSchedule({ ...schedule, [day]: updated });
                                    }}
                                />
                                <button
                                    onClick={() => {
                                        const updated = [...schedule[day]];
                                        updated.splice(i, 1);
                                        setSchedule({ ...schedule, [day]: updated });
                                    }}
                                >
                                    <FaTrash />
                                </button>
                            </div>
                        ))}
                        <button onClick={() => addSchedulePeriod(day)} style={{ marginTop: "4px" }}>
                            <FaPlusCircle /> Добавить интервал
                        </button>
                    </div>
                ))}
            </>
        );
    };

    return (
        <div style={styles.container}>
            <button style={styles.backButton} onClick={() => navigate(-1)}>
                <FaArrowLeft /> Назад
            </button>

            <h2 style={styles.title}>Добавить номер</h2>

            <input
                placeholder="+79991234567"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                style={styles.input}
            />
            <input
                placeholder="Имя (например: Гость Иван)"
                value={name}
                onChange={(e) => setName(e.target.value)}
                style={styles.input}
            />

            <select value={type} onChange={(e) => setType(e.target.value as any)} style={styles.input}>
                <option value="common">Обычный</option>
                <option value="temporary">Временный</option>
                <option value="schedule">По расписанию</option>
            </select>

            {type === "temporary" && (
                <>
                    <label>Время начала:</label>
                    <input
                        type="datetime-local"
                        value={startTime}
                        onChange={(e) => setStartTime(e.target.value)}
                        style={styles.input}
                    />
                    <label>Время конца:</label>
                    <input
                        type="datetime-local"
                        value={endTime}
                        onChange={(e) => setEndTime(e.target.value)}
                        style={styles.input}
                    />
                </>
            )}

            {type === "schedule" && renderScheduleEditor()}

            {error && <p style={styles.error}>{error}</p>}

            <button style={styles.saveButton} onClick={handleSave}>
                Сохранить номер
            </button>
        </div>
    );
};

const styles: { [key: string]: React.CSSProperties } = {
    container: {
        backgroundColor: "#fff6fa",
        minHeight: "100vh",
        width: "100vw",
        padding: "5vw",
        boxSizing: "border-box",
        fontFamily: "sans-serif",
    },
    title: {
        fontSize: "22px",
        fontWeight: "bold",
        marginBottom: "20px",
        color: "#5a4478",
    },
    input: {
        width: "100%",           // остаётся для адаптивности
        maxWidth: "400px",       // ограничивает максимальную ширину
        margin: "0 auto 12px",   // центрирует и задаёт отступ
        padding: "12px",
        fontSize: "16px",
        borderRadius: "8px",
        border: "1px solid #ccc",
        boxSizing: "border-box",
        display: "block",        // обязательно для margin auto
    },
    saveButton: {
        width: "50%",
        backgroundColor: "#5a4478",
        color: "#fff",
        padding: "14px",
        borderRadius: "20px",
        border: "none",
        cursor: "pointer",
        fontWeight: "bold",
        fontSize: "16px",
        margin: "0 auto 12px",
        display: "block", // ⬅️ обязательно для центрирования
    },
    error: {
        color: "red",
        fontSize: "14px",
        marginTop: "10px",
    },
    backButton: {
        background: "none",
        border: "none",
        color: "#5a4478",
        fontSize: "16px",
        cursor: "pointer",
        marginBottom: "20px",
        display: "flex",
        alignItems: "center",
        gap: "6px",
    },
};

export default AddPhonePage;
