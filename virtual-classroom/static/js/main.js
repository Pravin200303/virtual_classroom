document.addEventListener("DOMContentLoaded", () => {
    // --- Alert Notification Auto-Dismiss ---
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(alert => {
        // Auto dismiss after 4 seconds
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(100px)';
            alert.style.transition = 'all 0.5s ease';
            setTimeout(() => alert.remove(), 500);
        }, 4000);

        // Manual dismiss
        const closeBtn = alert.querySelector(".alert-close");
        if (closeBtn) {
            closeBtn.addEventListener("click", () => {
                alert.style.opacity = '0';
                alert.style.transform = 'translateX(100px)';
                alert.style.transition = 'all 0.3s ease';
                setTimeout(() => alert.remove(), 300);
            });
        }
    });

    // --- Signup Role Selection Toggles ---
    const roleOptions = document.querySelectorAll(".role-option");
    roleOptions.forEach(option => {
        option.addEventListener("click", () => {
            roleOptions.forEach(opt => opt.classList.remove("active"));
            option.classList.add("active");
            
            const radio = option.querySelector("input[type='radio']");
            if (radio) {
                radio.checked = true;
            }
        });
    });

    // --- Chart.js Analytics Dashboard (Interactive Charts) ---
    const ctx = document.getElementById("analyticsChart");
    if (ctx) {
        const totalCourses = parseInt(ctx.dataset.courses || 0);
        const totalStudents = parseInt(ctx.dataset.students || 0);
        const role = ctx.dataset.role || 'student';
        
        let labelData = [];
        let valData = [];
        let chartLabel = '';
        let gradientColorStart = 'rgba(99, 102, 241, 0.4)';
        let gradientColorEnd = 'rgba(99, 102, 241, 0.0)';
        let borderColor = '#6366f1';
        
        if (role === 'instructor') {
            labelData = ['Active Courses', 'Enrolled Students', 'Materials Uploaded'];
            valData = [totalCourses, totalStudents, totalCourses * 3]; // Mock relative uploads
            chartLabel = 'Classroom Overview';
        } else {
            labelData = ['Enrolled Courses', 'Available Courses', 'Completed Modules'];
            valData = [totalCourses, totalStudents, Math.floor(totalCourses * 1.5)];
            chartLabel = 'Study Progress';
            gradientColorStart = 'rgba(16, 185, 129, 0.4)';
            borderColor = '#10b981';
        }
        
        const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 200);
        gradient.addColorStop(0, gradientColorStart);
        gradient.addColorStop(1, gradientColorEnd);

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labelData,
                datasets: [{
                    label: chartLabel,
                    data: valData,
                    borderColor: borderColor,
                    borderWidth: 3,
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: borderColor,
                    pointBorderColor: '#fff',
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        },
                        ticks: {
                            color: '#a1a1aa',
                            font: {
                                family: 'Inter'
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        },
                        ticks: {
                            color: '#a1a1aa',
                            font: {
                                family: 'Inter'
                            }
                        }
                    }
                }
            }
        });
    }

    // --- Interactive Material Viewers (Video / PDF Embeds) ---
    const materialItems = document.querySelectorAll(".material-item[data-url]");
    const activeVideo = document.getElementById("activeVideo");
    const videoSource = document.getElementById("videoSource");
    const videoContainer = document.querySelector(".video-container");

    materialItems.forEach(item => {
        item.addEventListener("click", (e) => {
            // Prevent trigger if clicking download button
            if (e.target.closest('.btn-download')) {
                return;
            }
            
            const fileUrl = item.getAttribute("data-url");
            const fileType = item.getAttribute("data-type");

            if (fileType === 'video' && activeVideo && videoSource) {
                e.preventDefault();
                videoSource.src = fileUrl;
                activeVideo.load();
                if (videoContainer) {
                    videoContainer.style.display = 'block';
                    videoContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                activeVideo.play().catch(err => console.log("Video auto-play blocked: ", err));
            }
        });
    });
});
