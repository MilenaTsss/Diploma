import { useState } from "react";
import { useNavigate } from "react-router-dom";

const LoginUserPage: React.FC = () => {
  const [phone, setPhone] = useState("+7");
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (phone === "+7" || phone.length < 12) return;
    //TODO как появится ручка поменять на норм проверку
    // try {
    //    const response = await fetch("/user/check_admin", {
    //        method: "POST",
    //        headers: {
    //            "Content-Type": "application/json"
    //        },
    //        body: JSON.stringify({phone})
    //    });
    //
    //    const data = await response.json();
    let data = {
      is_admin: false,
    };
    if (phone == "+78005553535") {
      data.is_admin = true;
    }

    if (data.is_admin) {
      navigate("/verifyadmin");
    } else {
      navigate("/verifyuser");
    }
    // } catch (error) {
    //     console.error("Ошибка при проверке администратора:", error);
    // } // Перенаправление на страницу проверки кода (если нужно)
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value.replace(/\D/g, ""); // Удаляем все нецифровые символы

    if (value.length === 0) {
      setPhone(""); // Позволяет полностью стирать номер
      return;
    }

    if (!value.startsWith("7")) return;

    if (!value.startsWith("7")) {
      value = "7" + value.slice(1); // Принудительно ставим 7 в начало
    }
    value = "+" + value;
    setPhone(value.trim());
  };
  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>Вход</h2>
        <form onSubmit={handleSubmit} style={styles.form}>
          <label htmlFor="phone-input" style={styles.label}>
            Введите номер телефона
          </label>
          <input
            id="phone-input"
            type="text"
            value={phone}
            onChange={handleChange}
            maxLength={12}
            style={styles.input}
            required
            autoFocus
          />
          <button type="submit" style={styles.button}>
            Далее
          </button>
        </form>
      </div>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    height: "100vh",
    width: "100vw",
    backgroundColor: "#fef7fb",
    padding: "15px",
  },
  card: {
    backgroundColor: "#ffffff",
    padding: "5%",
    borderRadius: "15px",
    boxShadow: "0 4px 15px rgba(0, 0, 0, 0.1)",
    textAlign: "center",
    width: "90%",
    maxWidth: "400px",
  },
  title: {
    fontSize: "24px",
    marginBottom: "20px",
    color: "#5a4478",
    fontWeight: "bold",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    width: "100%",
  },
  label: {
    fontSize: "14px",
    marginBottom: "10px",
    color: "#666",
  },
  inputContainer: {
    width: "100%",
    marginBottom: "15px",
    display: "flex",
  },
  input: {
    width: "100%",
    fontSize: "16px",
    padding: "12px",
    borderRadius: "8px",
    border: "1px solid #ccc",
    outline: "none",
    transition: "border 0.3s ease",
    marginBottom: "15px",
  },
  button: {
    backgroundColor: "#5a4478",
    color: "#fff",
    border: "none",
    padding: "12px 20px",
    borderRadius: "25px",
    cursor: "pointer",
    fontSize: "16px",
    transition: "background 0.3s ease",
    width: "100%",
  },
};

export default LoginUserPage;
