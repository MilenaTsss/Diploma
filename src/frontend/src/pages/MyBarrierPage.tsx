import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FaArrowLeft, FaEdit, FaTrash, FaCheck, FaExclamation, FaClock } from "react-icons/fa";

const MyBarrierPage: React.FC = () => {
    const navigate = useNavigate();

    const additionalNumbers = [
        { name: "Мария Прогресс", phone: "+7 999 123 45 67", status: "time" },
        { name: "Мария Ошибка", phone: "+7 999 123 45 68", status: "error" },
        { name: "Мария Успех", phone: "+7 999 123 45 68", status: "ok" },
        { name: "Временный", phone: "+7 999 123 45 68", status: "time", start: "14 января 10:00", end: "14 января 18:00" },
        { name: "Расписание", phone: "+7 999 123 45 68", status: "time", schedule: ["Пн 10:00 - Пн 18:00", "Ср 10:00 - Ср 18:00"] },
    ];

    return (
        <div style={styles.page}>
            <div style={styles.header}>
                <button style={styles.backButton} onClick={() => navigate(-1)}>
                    <FaArrowLeft />
                </button>
                <h1 style={styles.title}>манежная площадь, 1, москва</h1>
            </div>

            <div style={styles.container}>
                {/* Инфо о шлагбауме */}
                <div style={styles.infoCard}>
                    <p>Администратор - Владимир Иванов</p>
                    <p>Телефон шлагбаума - +7 999 999 00 99</p>
                    <p>Телефон администратора - необязательно</p>
                    <h3 style={styles.sectionTitle}>Лимиты шлагбаума:</h3>
                    <div style={styles.limits}>
                        <div>Номеров - 4<br />Использовано - 2</div>
                        <div>Временных номеров - 1<br />Использовано - 1</div>
                        <div>Изменений в неделю - 10<br />Использовано - 5</div>
                    </div>
                </div>

                {/* Основной номер */}
                <h2 style={styles.subtitle}>Основной номер:</h2>
                <div style={styles.phoneCard}>
                    <span>Иван Иванов</span>
                    <span>+71111111111</span>
                </div>

                {/* Дополнительные номера */}
                <h2 style={styles.subtitle}>Дополнительные номера:</h2>

                {additionalNumbers.map((item, idx) => (
                    <div key={idx} style={styles.additionalCard}>
                        <div style={styles.row}>
                            <div>
                                <p style={styles.phoneName}>{item.name}</p>
                                <p>{item.phone}</p>
                                {item.start && item.end && (
                                    <p>Начало: {item.start}<br />Конец: {item.end}</p>
                                )}
                                {item.schedule && item.schedule.map((s, i) => (
                                    <p key={i}>Расписание: {s}</p>
                                ))}
                            </div>
                            <div style={styles.icons}>
                                <FaEdit style={styles.icon} />
                                <FaTrash style={styles.icon} />
                                {item.status === "ok" && <FaCheck style={styles.iconGreen} />}
                                {item.status === "error" && <FaExclamation style={styles.iconRed} />}
                                {item.status === "time" && <FaClock style={styles.iconClock} />}
                            </div>
                        </div>
                    </div>
                ))}

                {/* Кнопки снизу */}
                <div style={styles.buttonsRow}>
                    <button style={styles.mainButton}>Добавить номер</button>
                    <button style={styles.secondaryButton}>История изменений</button>
                </div>
            </div>
        </div>
    );
};

const styles: { [key: string]: React.CSSProperties } = {
    page: {
        backgroundColor: "#fef7fb",
        minHeight: "100vh",
        width: "100vw",
        padding: "20px",
        boxSizing: "border-box",
        fontFamily: "sans-serif",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
    },
    header: {
        display: "flex",
        alignItems: "center",
        gap: "10px",
        marginBottom: "20px",
        width: "100%",
        maxWidth: "600px",
    },
    backButton: {
        background: "none",
        border: "none",
        fontSize: "24px",
        color: "#5a4478",
        cursor: "pointer",
    },
    title: {
        fontSize: "24px",
        fontWeight: "bold",
        color: "#5a4478",
    },
    container: {
        width: "100%",
        maxWidth: "600px",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
    },
    infoCard: {
        backgroundColor: "#fff",
        padding: "20px",
        borderRadius: "16px",
        boxShadow: "0 4px 12px rgba(90,68,120,0.1)",
    },
    sectionTitle: {
        marginTop: "15px",
        fontSize: "18px",
        color: "#5a4478",
        fontWeight: "bold",
    },
    limits: {
        display: "flex",
        justifyContent: "space-between",
        marginTop: "10px",
        fontSize: "14px",
    },
    subtitle: {
        fontSize: "20px",
        fontWeight: "bold",
        color: "#5a4478",
        marginBottom: "5px",
        marginTop: "10px",
    },
    phoneCard: {
        backgroundColor: "#fff",
        padding: "15px",
        borderRadius: "12px",
        boxShadow: "0 4px 8px rgba(90,68,120,0.1)",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
    },
    additionalCard: {
        backgroundColor: "#fff",
        padding: "15px",
        borderRadius: "12px",
        boxShadow: "0 4px 8px rgba(90,68,120,0.1)",
    },
    row: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
    },
    phoneName: {
        fontWeight: "bold",
        color: "#333",
        marginBottom: "5px",
    },
    icons: {
        display: "flex",
        flexDirection: "column",
        gap: "8px",
        alignItems: "flex-end",
    },
    icon: {
        fontSize: "18px",
        color: "#5a4478",
        cursor: "pointer",
    },
    iconGreen: {
        fontSize: "18px",
        color: "green",
    },
    iconRed: {
        fontSize: "18px",
        color: "red",
    },
    iconClock: {
        fontSize: "18px",
        color: "#f0a500",
    },
    buttonsRow: {
        display: "flex",
        justifyContent: "space-between",
        marginTop: "20px",
        gap: "10px",
    },
    mainButton: {
        flex: 1,
        padding: "14px",
        backgroundColor: "#5a4478",
        color: "#fff",
        border: "none",
        borderRadius: "25px",
        fontWeight: "bold",
        fontSize: "16px",
        cursor: "pointer",
    },
    secondaryButton: {
        flex: 1,
        padding: "14px",
        backgroundColor: "#d7c4ed",
        color: "#5a4478",
        border: "none",
        borderRadius: "25px",
        fontWeight: "bold",
        fontSize: "16px",
        cursor: "pointer",
    },
};

export default MyBarrierPage;
