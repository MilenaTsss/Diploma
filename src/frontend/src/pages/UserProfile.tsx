import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";

const UserProfile: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [name, setName] = useState("Загрузка...");
  const [phone, setPhone] = useState(() => location.state?.phone || "");
  const [isEditingName, setIsEditingName] = useState(false);
  const [isEditingPhone, setIsEditingPhone] = useState(false);
  const [requestSent, setRequestSent] = useState(false);
  const [showSwitch, setShowSwitch] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  const [accessToken, setAccessToken] = useState(
    () => location.state?.access_token || localStorage.getItem("access_token"),
  );
  const [refreshToken, setRefreshToken] = useState(
    () =>
      location.state?.refresh_token || localStorage.getItem("refresh_token"),
  );

  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const meResponse = await fetch("/api/users/me/", {
          headers: {
            Authorization: `Bearer ${accessToken}`,
            Accept: "application/json",
          },
        });

        if (meResponse.ok) {
          const userData = await meResponse.json();
          setName(userData.full_name || "Без имени");
          setPhone(userData.phone || "-");
          checkAdmin(userData.phone);
        } else {
          const refreshResponse = await fetch("/auth/token/refresh/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh: refreshToken }),
          });

          const refreshData = await refreshResponse.json();

          if (refreshResponse.ok && refreshData.access) {
            const newAccessToken = refreshData.access;
            setAccessToken(newAccessToken);
            localStorage.setItem("access_token", newAccessToken);

            const retryResponse = await fetch("/api/users/me/", {
              headers: {
                Authorization: `Bearer ${newAccessToken}`,
                Accept: "application/json",
              },
            });

            if (retryResponse.ok) {
              const userData = await retryResponse.json();
              setName(userData.full_name || "Без имени");
              setPhone(userData.phone || "-");
            } else {
              throw new Error("Не удалось загрузить профиль");
            }
          } else {
            navigate("/login");
          }
        }
      } catch (err) {
        console.error("Ошибка при получении профиля:", err);
        navigate("/login");
      }
    };

    fetchUserProfile();
  }, [accessToken, refreshToken, navigate]);

  const checkAdmin = async (userPhone: string) => {
    try {
      const response = await fetch("/api/users/check_admin/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ phone: userPhone }),
      });
      const data = await response.json();
      if (response.ok && data.is_admin) {
        setShowSwitch(true);
      }
    } catch (error) {
      console.error("Ошибка при проверке администратора:", error);
    }
  };

  const handleSave = async () => {
    try {
      const patchResponse = await fetch("/api/users/me/", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          full_name: name,
          phone_privacy: "public",
        }),
      });

      if (patchResponse.ok) {
        const updatedData = await patchResponse.json();
        setName(updatedData.full_name || "Без имени");
        setRequestSent(true);
        setTimeout(() => {
          setRequestSent(false);
          setIsEditingName(false);
        }, 2000);
      } else {
        console.error("Ошибка обновления профиля");
      }
    } catch (error) {
      console.error("Ошибка сети при сохранении:", error);
    }
  };

  const navigateWithState = (path: string) => {
    navigate(path, {
      state: {
        phone,
        access_token: accessToken,
        refresh_token: refreshToken,
      },
    });
  };

  const handleRoleSwitch = () => {
    if (isAdmin) {
      navigate("/user", {
        state: { phone, access_token: accessToken, refresh_token: refreshToken },
      });
    } else {
      navigate("/admin", {
        state: { phone, access_token: accessToken, refresh_token: refreshToken },
      });
    }
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Профиль</h2>

      <div style={styles.card}>
        {isEditingName ? (
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            style={styles.input}
          />
        ) : (
          <p style={styles.text}>{name || "—"}</p>
        )}
        <button
          style={styles.button}
          onClick={() => {
            isEditingName ? handleSave() : setIsEditingName(true);
          }}
        >
          {isEditingName
            ? requestSent
              ? "Сохранено"
              : "Сохранить"
            : "Изменить имя в профиле"}
        </button>
      </div>

      <div style={styles.card}>
        <p style={styles.text}>{phone || "—"}</p>
        <button
          style={styles.button}
          onClick={() => navigateWithState("/change-phone")}
        >
          Изменить номер телефона
        </button>
      </div>

      <div style={styles.switchBlock}>
        <span style={!isAdmin ? styles.activeText : styles.inactiveText}>Пользователь</span>
        <label style={styles.switch}>
          <input
              type="checkbox"
              checked={isAdmin}
              onChange={() => {
                setIsAdmin((prev) => !prev);
                handleRoleSwitch();
              }}
              style={styles.switchInput}
          />
          <span
              style={{
                ...styles.slider,
                ...(isAdmin ? styles.switchChecked : {}),
              }}
          >
      <span
          style={{
            ...styles.sliderBefore,
            ...(isAdmin ? styles.switchCheckedBefore : {}),
          }}
      />
    </span>
        </label>
        <span style={isAdmin ? styles.activeText : styles.inactiveText}>Администратор</span>
      </div>




      <div style={styles.navbar}>
        <button
          style={styles.navButton}
          onClick={() =>
            navigate("/barriers", {
              state: {
                phone,
                access_token: accessToken,
                refresh_token: refreshToken,
              },
            })
          }
        >
          Шлагбаумы
        </button>
        <button
          style={styles.navButton}
          onClick={() =>
            navigate("/requests", {
              state: {
                phone,
                access_token: accessToken,
                refresh_token: refreshToken,
              },
            })
          }
        >
          Запросы
        </button>
        <button style={{ ...styles.navButton, ...styles.navButtonActive }}>
          Профиль
        </button>
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
    color: "#333333",
    padding: "20px",
  },
  title: {
    fontSize: "24px",
    fontWeight: "bold",
    color: "#5a4478",
    marginBottom: "20px",
  },
  card: {
    backgroundColor: "#ffffff",
    padding: "15px",
    borderRadius: "10px",
    boxShadow: "0 4px 10px rgba(90, 68, 120, 0.2)",
    textAlign: "center",
    width: "90%",
    maxWidth: "400px",
    marginBottom: "20px",
  },
  text: {
    fontSize: "18px",
    marginBottom: "10px",
  },
  input: {
    width: "100%",
    fontSize: "16px",
    padding: "10px",
    borderRadius: "8px",
    border: "1px solid #ccc",
    outline: "none",
    marginBottom: "10px",
    backgroundColor: "#ffffff",
    color: "#333333",
  },
  button: {
    backgroundColor: "#5a4478",
    color: "#ffffff",
    border: "none",
    padding: "10px 15px",
    borderRadius: "20px",
    cursor: "pointer",
    fontSize: "14px",
    width: "100%",
  },
  switchBlock: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    marginTop: "20px",
    gap: "10px",
    color: "#5a4478",
  },
  navbar: {
    display: "flex",
    justifyContent: "space-around",
    width: "100%",
    position: "fixed",
    bottom: "0",
    backgroundColor: "#f8f3fb",
    padding: "10px 0",
  },
  navButton: {
    background: "none",
    border: "none",
    fontSize: "14px",
    color: "#5a4478",
    cursor: "pointer",
  },
  navButtonActive: {
    borderBottom: "2px solid #5a4478",
    paddingBottom: "4px",
  },
  activeNavButton: {
    borderBottom: "2px solid #5a4478",
    paddingBottom: "4px",
  },
  switch: {
    position: "relative",
    display: "inline-block",
    width: "50px",
    height: "24px",
  },
  slider: {
    position: "absolute",
    cursor: "pointer",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "#ccc",
    borderRadius: "24px",
    transition: "0.4s",
  },
  sliderBefore: {
    position: "absolute",
    content: "''",
    height: "18px",
    width: "18px",
    left: "3px",
    bottom: "3px",
    backgroundColor: "white",
    transition: "0.4s",
    borderRadius: "50%",
  },
  switchInput: {
    opacity: 0,
    width: 0,
    height: 0,
  },
  switchChecked: {
    backgroundColor: "#5a4478",
  },
  switchCheckedBefore: {
    transform: "translateX(26px)",
  },

};

export default UserProfile;
