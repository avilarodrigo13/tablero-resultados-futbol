import os
import sys
import paramiko
from scp import SCPClient

def main():
    host = "192.168.0.50"
    user = "truenas_admin"
    secret = "789456"
    nas_dir = "/mnt/Apps/tablero"
    
    local_dir = os.path.dirname(os.path.abspath(__file__))
    files_to_upload = [
        "index.html",
        "style.css",
        "app.js",
        "logo_tdf.png",
        "updater.py"
    ]
    
    print(f"Estableciendo conexión SSH con {user}@{host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        key_ed25519 = os.path.expanduser("~/.ssh/id_ed25519")
        key_rsa = os.path.expanduser("~/.ssh/id_rsa")
        
        if os.path.exists(key_ed25519):
            ssh.connect(hostname=host, username=user, key_filename=key_ed25519, timeout=10)
        elif os.path.exists(key_rsa):
            ssh.connect(hostname=host, username=user, key_filename=key_rsa, timeout=10)
        else:
            ssh.connect(hostname=host, username=user, password=secret, timeout=10)
            
        print("¡Conexión SSH establecida con éxito!")
        
        # Iniciar cliente SFTP/SCP
        print("Iniciando transferencia de archivos via SCP...")
        with SCPClient(ssh.get_transport()) as scp:
            for file_name in files_to_upload:
                local_path = os.path.join(local_dir, file_name)
                remote_path = f"{nas_dir}/{file_name}"
                if os.path.exists(local_path):
                    print(f"Subiendo {file_name} -> {remote_path}...")
                    scp.put(local_path, remote_path)
                else:
                    print(f"Error: No se encontró el archivo local {local_path}")
                    
        print("¡Todos los archivos fueron transferidos exitosamente!")
        
        # Ejecutar el actualizador en el NAS para verificar
        cmd = f"python3 {nas_dir}/updater.py {nas_dir}/partidos.json"
        print(f"Ejecutando actualizador en el NAS: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        out = stdout.read().decode('utf-8')
        err = stderr.read().decode('utf-8')
        
        if out:
            print(f"Salida del NAS:\n{out}")
        if err:
            print(f"Errores del NAS:\n{err}")
            
        print("Despliegue finalizado con éxito.")
        
    except Exception as e:
        print(f"Error durante el despliegue: {e}")
        sys.exit(1)
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
