import socket

def read_novatel_tcp(host="192.168.3.22", port=2000):
    """ Read Novatel GPS data through TCP """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        print(f"Connected to {host}:{port}")

        while True:
            data = sock.recv(4096).decode("ascii", errors="ignore").strip()
            if data:
                print(data)
                if data.startswith("$GPGGA"):
                    print(parse_gpgga(data))
                if data.startswith("#BESTPOSA"):
                    print(parse_bestposa(data))
                if data.startswith("#INSPVAA"):
                    print(parse_inspva(data))
                # print(data[1]+data[2]+data[3]+data[4]+data[5]+data[6])

    except socket.error as e:
        print(f"Socket error: {e}")
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        if "sock" in locals():
            sock.close()


def parse_gpgga(gpgga_str):
    """Decode $GPGGA"""
    # if not gpgga_str.startswith("$GPGGA"):
    #     return None

    parts = gpgga_str.split(",")
    if len(parts) < 10:
        return None

    try:
        lat = float(parts[2][:2]) + float(parts[2][2:]) / 60  # convert to decimal
        lon = float(parts[4][:3]) + float(parts[4][3:]) / 60  # convert to decimal
        alt = float(parts[9])  # altitude
        return {"latitude": lat, "longitude": lon, "altitude": alt}
    except (ValueError, IndexError):
        return None


def parse_bestposa(bestposa_str):
    """Decode BESTPOSA"""
    # if not bestposa_str.startswith("#BESTPOSA"):
    #     return None

    # parts = bestposa_str.split(";")[0].split(",")
    parts = bestposa_str.split(",")
    if len(parts) < 12:
        return None

    try:
        lat = float(parts[11])
        lon = float(parts[12])
        alt = float(parts[13])
        status = parts[5]
        return {"latitude": lat, "longitude": lon, "altitude": alt, "status": status}
    except (ValueError, IndexError):
        return None
    
def parse_inspva(inspva_str):
    """Decode inspva"""
    # if not bestposa_str.startswith("#BESTPOSA"):
    #     return None

    # parts = bestposa_str.split(";")[0].split(",")
    parts = inspva_str.split(",")
    print(len(parts))
    if len(parts) < 12:
        return None

    try:
        lat = float(parts[11])
        lon = float(parts[12])
        yaw = float(parts[19])
        status = parts[5]
        return {"latitude": lat, "longitude": lon, "altitude": yaw, "status": status}
    except (ValueError, IndexError):
        return None

if __name__ == "__main__":
    read_novatel_tcp()