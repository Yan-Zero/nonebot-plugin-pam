import Cookies from "js-cookie";

function checkAuthKey() {
  return Cookies.get("auth_key");
}

export default checkAuthKey;
