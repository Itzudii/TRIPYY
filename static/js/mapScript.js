

class MapHandler {
    constructor() {
        this.apiKey = "Zl6uQG-1R_LuHSw9jdlDODppJXGeZoLlLTuFzK5-HFk";
        this.trafficLayer = null;
        this.pointcoord = null;
        this.activatekey = "gps";
        this.usercoord = null;
        this.markers = {};
        this.currentSearchdata = null;
        this.previousRouteGroup = null;
        
        
        // Initialize the platform
        this.platform = new H.service.Platform({ apikey: this.apiKey });
        this.defaultLayers = this.platform.createDefaultLayers();
        
        // Create the map=======================
        this.map = new H.Map(
            document.getElementById("map"),
            this.defaultLayers.vector.normal.map,
            {
                zoom: 14,
                center: { lat: 52.5200, lng: 13.4050 }
            }
        );
        

        this.group = new H.map.Group();
        this.map.addObject(this.group);

        this.map.addEventListener('mapviewchangeend', () => {
            var currentZoom = this.map.getZoom();
            if (currentZoom >= 14) {
                var data = this.currentSearchdata;
                if (data) {

                    this.group.removeAll();
                    for (let i = 0; i < data.features.length; i++) {
                        var coord = data.features[i].geometry.coordinates;
                        var detail = data.features[i].properties.name;
                        var obj = this.addtags(coord[1], coord[0], detail);
                        this.group.addObject(obj);


                    }
                }
            } else {
                this.group.removeAll();
            }
        });

        // Add UI & Behavior Controls
        this.ui = H.ui.UI.createDefault(this.map, this.defaultLayers);
        this.mapSettingsControl = this.ui.getControl('mapsettings');
        this.mapSettingsControl.setVisibility(false);
        this.behavior = new H.mapevents.Behavior(new H.mapevents.MapEvents(this.map));

        // Search elements
        this.searchBtn = document.querySelector(".search-div-div button");
        this.searchInput = document.querySelector(".search-div-div input");

        // Add event listeners
        this.searchBtn.addEventListener("click", () => this.searchLocation(this.searchInput.value));
        document.getElementById("traffic_btn").addEventListener("click", () => this.toggleTrafficLayer());
        document.getElementById("route_btn").addEventListener("click", () => this.setroute());
        document.getElementById("currentLoc_btn").addEventListener("click", () => this.setCurrentLocation());

        // Add Click Event for Latitude & Longitude
        this.addClickEventListener();

        try {
            const coordinatesElement = document.getElementById('coordinates');
            const coordsList = JSON.parse(coordinatesElement.getAttribute('data-coords'));
            this.map.setCenter({ lat: coordsList['coord'][0], lng: coordsList['coord'][1] });
            coordsList['data'].forEach(place => {
                this.addBoxMarker(place.lat, place.lng, place.name);
            })
            
        } catch (error) {
            console.error("Error parsing coordinates:", error);
            return;
            
        }
    }

    // search location method
    async searchLocation(city) {
        try {
            const response = await fetch(`https://geocode.search.hereapi.com/v1/geocode?q=${encodeURIComponent(city)}&apiKey=${this.apiKey}`);
            const data = await response.json();

            if (data.items.length > 0) {
                const coords = data.items[0].position;
                this.map.setCenter(coords);
                this.map.setZoom(15);

            } else {
                console.log("City not found");
            }
            this.getTagsData().then(data => {
                this.currentSearchdata = data;
            });
        } catch (error) {
            console.error("Error fetching geocode:", error);
        }

    }
    // toggle traffic layer
    toggleTrafficLayer() {
        if (!this.trafficLayer) {
            this.trafficLayer = this.defaultLayers.vector.traffic.map;
            this.map.addLayer(this.trafficLayer);
        } else {
            this.map.removeLayer(this.trafficLayer);
            this.trafficLayer = null;
        }
    }
    
    // click event on map method
    addClickEventListener() {
        this.map.addEventListener("tap", (evt) => {
            const coord = this.map.screenToGeo(evt.currentPointer.viewportX, evt.currentPointer.viewportY);
            this.pointcoord = coord;

            // Remove existing markers
            // this.map.getObjects().forEach(obj => this.map.removeObject(obj));
            if (this.markers["pointer"]) {

                this.map.removeObject(this.markers["pointer"]);
                delete this.markers["pointer"];
            }

            // Add marker at clicked position (for all)
            var marker = new H.map.Marker(coord);
            this.markers["pointer"] = marker
            this.map.addObject(this.markers["pointer"]);

        });
    }

    addBoxMarker(lat, lng, text) {
        var boxSVG = `<svg width="30" height="30" xmlns="http://www.w3.org/2000/svg">
                        <rect width="30" height="30" style="fill: red; stroke: black; stroke-width: 2;" />
                        </svg>`;
        var boxIcon = new H.map.Icon(boxSVG, { size: { w: 10, h: 10 } });
        var marker = new H.map.Marker({ lat: lat, lng: lng }, { icon: boxIcon });
        this.map.addObject(marker);

        var bubble = new H.ui.InfoBubble({ lat: lat, lng: lng }, { content: `<b>${text}</b>` });

        marker.addEventListener('pointerenter', ()=> {
            this.ui.addBubble(bubble);
        });

        marker.addEventListener('pointerleave',()=> {
            this.ui.removeBubble(bubble);
        });
    }

    // display directions or route method
    displayDirections() {
        const origin = this.usercoord;
        const destination = this.pointcoord;

        const routingParameters = {
            routingMode: "fast",
            transportMode: "car",
            origin: `${origin.lat},${origin.lng}`,
            destination: `${destination.lat},${destination.lng}`,
            return: "polyline",
        };

        const onResult = (result) => {
            if (result.routes.length) {
                const lineStrings = [];
                result.routes[0].sections.forEach((section) => {
                    lineStrings.push(H.geo.LineString.fromFlexiblePolyline(section.polyline));
                });

                const multiLineString = new H.geo.MultiLineString(lineStrings);

                const routeLine = new H.map.Polyline(multiLineString, {
                    style: {
                        strokeColor: "blue",
                        lineWidth: 3,
                    },
                });

                const startMarker = new H.map.Marker(origin);
                const endMarker = new H.map.Marker(destination);

                if (this.previousRouteGroup) {
                    this.map.removeObject(this.previousRouteGroup);
                }


                const group = new H.map.Group();
                group.addObjects([routeLine, startMarker, endMarker]);
                this.map.addObject(group);

                this.previousRouteGroup = group;

                this.map.getViewModel().setLookAtData({
                    bounds: group.getBoundingBox(),
                });
            }
        };

        const router = this.platform.getRoutingService(null, 8);

        router.calculateRoute(routingParameters, onResult, function (error) {
            alert(error.message);
        });
    }

    async setCurrentLocation() {
        await this.getCurrentLocation();
        const svgMarkup = '<svg width="24" height="24" xmlns="http://www.w3.org/2000/svg">' +
            '<circle cx="12" cy="12" r="10" fill="red" stroke="black" stroke-width="2" />' +
            '</svg>';

        // icon for gps
        const icon = new H.map.Icon(svgMarkup);
        this.map.setCenter(this.usercoord);
        this.map.setZoom(15);

        const marker = new H.map.Marker(this.usercoord, { icon: icon });
        this.map.addObject(marker);

    }
    // use await to get current location in sync... way
    async setroute() {
        await this.getCurrentLocation();
        this.displayDirections()

    }
    async getCurrentLocation() {
        if (!navigator.geolocation) {
            console.log("Geolocation is not supported by this browser.");
            return null;
        }

        return new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const coords = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    };
                    this.usercoord = coords;
                    resolve(coords); // Resolve the Promise with coordinates
                },
                (error) => {
                    console.error("Error getting location:", error);
                    reject(error);
                }
            );
        });
    }

    addtags(p_lat, p_lng, p_name) {
        var tag = new H.map.Marker({ lat: p_lat, lng: p_lng });
        tag.setData(`Hotel Name: ${p_name}`);
        return tag;
    }
    async getTagsData() {
        var current = this.map.getCenter();
        const url = `https://opentripmap-places-v1.p.rapidapi.com/en/places/radius?radius=500&lon=${current.lng}&lat=${current.lat}`;
        const options = {
            method: 'GET',
            headers: {
                'x-rapidapi-key': 'ccdcc632fbmshf1695b1d81acb0ap19661djsnbbe99873dacd',
                'x-rapidapi-host': 'opentripmap-places-v1.p.rapidapi.com'
            }
        };

        try {
            const response = await fetch(url, options);
            const result = await response.json();
            return result;
        } catch (error) {
            console.error(error);
        }
    }



}

window.addEventListener("load", () => {
    new MapHandler();
});