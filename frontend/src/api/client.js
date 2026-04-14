import axios from "axios";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8080/api",
});

export const getNationalTrend = (params) =>
  API.get("/national/trend", { params });

export const getCounties = () => API.get("/counties");

export const getCountyHistory = (name) =>
  API.get(`/county/${name}/history`);

export const getFilters = () => API.get("/filters");

export default API;