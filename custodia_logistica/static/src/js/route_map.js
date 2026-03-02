(function () {
    "use strict";

    console.log("Custodia Logística: Iniciando carga de mapas duales...");

    document.addEventListener("DOMContentLoaded", function () {
        // Ejecutamos la carga con un retraso escalonado para evitar conflictos
        setTimeout(() => {
            initPlannedRouteMap();
        }, 300);

        setTimeout(() => {
            initLiveTrackingMap();
        }, 800);
    });

    // --- 1. FUNCIÓN MAPA RUTA PLANEADA ---
async function initPlannedRouteMap() {
    const container = document.getElementById("route-map");
    if (!container || !container.dataset.rutaId) return;

    const rutaId = container.dataset.rutaId;

    try {
        const response = await fetch("/custodia/ruta/" + rutaId + "/coordinates", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ params: {} })
        });

        const data = await response.json();
        const coords = data.result;

        if (!coords || coords.length < 2) return;

        const origin = coords[0];
        const destination = coords[coords.length - 1];

        const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${origin.lng},${origin.lat};${destination.lng},${destination.lat}?overview=full&geometries=geojson`;

        const routeResponse = await fetch(osrmUrl);
        const routeData = await routeResponse.json();

        if (!routeData.routes || routeData.routes.length === 0) return;

        const routeGeo = routeData.routes[0].geometry;

        const mapRoute = L.map("route-map").setView([origin.lat, origin.lng], 6);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(mapRoute);

        const routeLayer = L.geoJSON(routeGeo, {
            style: { color: "blue", weight: 5 }
        }).addTo(mapRoute);

        mapRoute.fitBounds(routeLayer.getBounds());

        setTimeout(() => mapRoute.invalidateSize(), 200);

    } catch (e) {
        console.error("Error en Mapa de Ruta:", e);
    }
}

    // --- 2. FUNCIÓN MAPA MONITOREO EN VIVO ---
    function initLiveTrackingMap() {
        const container = document.getElementById("live-map");
        if (!container) return;

        const serviceId = container.dataset.serviceId;
        const token = container.dataset.token;
        
        // Instancia única para el mapa en vivo
        const mapLive = L.map('live-map').setView([19.4326, -99.1332], 5);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(mapLive);
        
        let marker = L.marker([19.4326, -99.1332]).addTo(mapLive).bindPopup("Esperando señal...");

        async function updatePos() {
            try {
                const res = await fetch(`/mis-servicios/${serviceId}/tracking?access_token=${token}`);
                const data = await res.json();
                if (data.lat && data.lng) {
                    const pos = [data.lat, data.lng];
                    marker.setLatLng(pos).setPopupContent("Última actualización: " + (data.last_update || "Reciente"));
                    mapLive.panTo(pos);
                }
            } catch (e) { console.error("Error en Actualización en Vivo:", e); }
        }
        
        setTimeout(() => {
            mapLive.invalidateSize();
            updatePos();
        }, 300);
        
        // Actualización cada 30 segundos para no saturar el servidor
        setInterval(updatePos, 30000);
    }
})();
