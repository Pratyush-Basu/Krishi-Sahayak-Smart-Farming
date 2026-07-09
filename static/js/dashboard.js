// STEP 8: Dashboard Auth Protection + Logout + Slideshow

import { auth } from "./firebase.js";
import { onAuthStateChanged, signOut } 
from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

// 🔐 Protect Dashboard (VERY IMPORTANT)
onAuthStateChanged(auth, (user) => {
  if (!user) {
    // If not logged in, redirect to login page
    window.location.href = "login.html";
  }
});

// 🚪 Logout using Firebase
function logout() {
  signOut(auth).then(() => {
    window.location.href = "landing.html";
  });
}

// Make logout accessible from HTML onclick
window.logout = logout;

// 🎞️ Slideshow logic (UNCHANGED)
let currentSlide = 0;

function showSlide(index) {
  const slides = document.querySelectorAll(".slide");
  slides.forEach((slide, i) => {
    slide.classList.toggle("active", i === index);
  });
}

function startSlideshow() {
  const slides = document.querySelectorAll(".slide");
  if (slides.length === 0) return;

  showSlide(currentSlide);
  setInterval(() => {
    currentSlide = (currentSlide + 1) % slides.length;
    showSlide(currentSlide);
  }, 5000);
}

// Start slideshow when dashboard loads
startSlideshow();



// 🔄 Animated Farmer Names
const farmerNames = [
  { name: "अन्नदाता (Annadata)", color: "#2e8b57" },
  { name: "Kisan Dada", color: "#ff8c00" },
  { name: "Krishi Mitra", color: "#1e90ff" },
  { name: "Farmer Bhai", color: "#8b0000" }
];

let index = 0;
const nameElement = document.getElementById("farmerName");

if (nameElement) {
  setInterval(() => {
    index = (index + 1) % farmerNames.length;
    nameElement.textContent = farmerNames[index].name;
    nameElement.style.color = farmerNames[index].color;

    nameElement.style.animation = "none";
    nameElement.offsetHeight; // reflow
    nameElement.style.animation = "fadeSlide 1s ease-in-out";
  }, 2000);
}