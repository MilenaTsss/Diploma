import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { FaArrowLeft, FaTrash, FaPlusCircle } from "react-icons/fa";

const EditPhonePage: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const phoneId = location.state?.phone_id;
    const original = location.state?.phone_data;
    const accessToken = location.state?.access_token;

    const [name, setName] = useState(original?.name || "");
    const [startTime, setStartTime] = useState(original?.start_time || "");
    const [endTime, setEndTime] = useState(original?.end_time || "");
    const [schedule, setSchedule] = useState(original?.schedule || {
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

        if (!name) {
            setError("Введите имя.");
            return;
        }

        try {
            if (original.type === "common" || original.type === "temporary") {
                const patchBody: any = { name };
                if (original.type === "temporary") {
                    if (!startTime || !endTime) {
                        setError("Укажите время начала и конца.");
                        return;
                    }
                    if (new Date(startTime) >= new Date(endTime)) {
                        setError("Время начала должно быть раньше конца.");
                        return;
                    }
                    patchBody.start_time = startTime;
                    patchBody.end_time = endTime;
                }

                const res = await fetch(`/api/phones/${phoneId}/`, {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${accessToken}`,
                    },
                    body: JSON.stringify(patchBody),
                });

                if (!res.ok) {
                    const data = await res.json();
                    setError(data.detail || "Ошибка обновления номера.");
                    return;
                }
            }

            if (original.type === "schedule") {
                const res = await fetch(`/api/phones/${phoneId}/schedule/`, {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${accessToken}`,
                    },
                    body: JSON.stringify(schedule),
                });

                if (!res.ok) {
                    const data = await res.json();
                    setError(data.detail || "Ошибка обновления расписания.");
                    return;
                }
            }

            navigate(-1);
        } catch {
            setError("Ошибка сети");
        }
    };

    const addSchedulePeriod = (day: string) => {
        const updated = { ...schedule };
        updated[day].push({ start_time: "08:00", end_time: "12:00" });
        setSchedule(updated);
    };

    const renderScheduleEditor = () => (
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
                            <button onClick={() => {
                                const updated = [...schedule[day]];
                                updated.splice(i, 1);
                                setSchedule({ ...schedule, [day]: updated });
                            }}>
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

    return (
        <div style={styles.container}>
            <button style={styles.backButton} onClick={() => navigate(-1)}>
                <FaArrowLeft /> Назад
            </button>

            <h2 style={styles.title}>Редактировать номер</h2>

            <input
                placeholder="Имя"
                value={name}
                onChange={(e) => setName(e.target.value)}
                style={styles.input}
            />

            {original.type === "temporary" && (
                <>
                    <label>Начало:</label>
                    <input
                        type="datetime-local"
                        value={startTime}
                        onChange={(e) => setStartTime(e.target.value)}
                        style={styles.input}
                    />
                    <label>Конец:</label>
                    <input
                        type="datetime-local"
                        value={endTime}
                        onChange={(e) => setEndTime(e.target.value)}
                        style={styles.input}
                    />
                </>
            )}

            {original.type === "schedule" && renderScheduleEditor()}

            {error && <p style={styles.error}>{error}</p>}

            <button style={styles.saveButton} onClick={handleSave}>
                Сохранить изменения
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
        fontFamily: "sans-serif",
        boxSizing: "border-box",
    },
    title: {
        fontSize: "22px",
        fontWeight: "bold",
        marginBottom: "20px",
        color: "#5a4478",
    },
    input: {
        width: "100%",
        maxWidth: "400px",
        display: "block",
        margin: "0 auto 12px",
        padding: "12px",
        fontSize: "16px",
        borderRadius: "8px",
        border: "1px solid #ccc",
        boxSizing: "border-box",
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
        margin: "0 auto",
        display: "block",
    },
    error: {
        color: "red",
        fontSize: "14px",
        textAlign: "center",
        marginBottom: "10px",
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

export default EditPhonePage;
