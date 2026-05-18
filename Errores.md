# 🛠️ Guía de Solución de Problemas (Troubleshooting)

Durante el despliegue, configuración y pruebas de resiliencia de la infraestructura en Kubernetes, se registraron diversos incidentes técnicos. A continuación, se detalla la recopilación completa de todos los errores detectados, sus causas raíz y las soluciones aplicadas para resolverlos.

---

### 1. Error al consultar métricas de hardware
**Error:**
```text
error: Metrics API not available
```
**Causa:** Ocurre inmediatamente después de activar el addon del servidor de métricas (`minikube addons enable metrics-server`). El componente tarda entre 1 y 2 minutos en inicializarse, descubrir los recursos del clúster y recopilar la primera ronda de telemetría de CPU y memoria.
**Solución:** Esperar de 60 a 120 segundos para permitir que la API recopile datos y volver a ejecutar el comando de diagnóstico:
```bash
kubectl top pods
```

---

### 2. Inundación de respuestas 404 en la prueba de carga
**Error:**
```text
wget: server returned error: HTTP/1.1 404 Not Found
```
**Causa:** El pod generador de estrés (`busybox`) realiza peticiones HTTP GET a la ruta raíz (`http://chat-backend:8000/`). Como el backend en FastAPI no tiene expuesta ninguna ruta en el endpoint raíz (`/`), el servidor responde correctamente con un código de estado 404. Aunque la carga de procesamiento se genera con éxito, el output satura visualmente la terminal.
**Solución:** Redirigir las peticiones a un endpoint válido que consuma recursos (como la documentación interactiva) y descartar el output redirigiéndolo a la basura del sistema (`/dev/null`):
```bash
kubectl run -i --tty atacante --rm --image=busybox --restart=Never -- /bin/sh -c "while true; do wget -q -O /dev/null http://chat-backend:8000/docs; done"
```

---

### 3. Conflicto de duplicidad en pods efímeros
**Error:**
```text
Error from server (AlreadyExists): pods "load-generator" already exists
```
**Causa:** Al interrumpir la prueba de estrés con `Ctrl + C`, Kubernetes inicia la terminación del pod. Si se intenta ejecutar el comando de ataque inmediatamente con el mismo nombre, el clúster rechaza la solicitud porque el pod viejo se encuentra en su periodo de gracia de eliminación (*Grace Period*) y el identificador sigue ocupado.
**Solución:** Modificar de forma secuencial el nombre del pod atacante (por ejemplo, `load-generator-2`) o esperar 30 segundos a que el recolector de basura (*Garbage Collector*) de Kubernetes libere el recurso por completo.

---

### 4. Bloqueo por Firewall (403 Forbidden) en descarga de manifiestos
**Error:**
```text
error: unable to read URL "[https://mirrors.chaos-mesh.org/](https://mirrors.chaos-mesh.org/)...": server reported 403 Forbidden
# O en PowerShell de Windows:
Invoke-WebRequest : Error en el servidor remoto: (403) Prohibido.
```
**Causa:** Las políticas de seguridad y los firewalls perimetrales (como Cloudflare) del proveedor bloquean las peticiones automatizadas provenientes de herramientas de línea de comandos como `kubectl` o scripts de PowerShell para evitar ataques de denegación de servicio.
**Solución:** Omitir la descarga directa del manifiesto plano e instalar la infraestructura de manera nativa utilizando **Helm**, el gestor de paquetes corporativo de Kubernetes, lo que permite negociar la instalación de forma segura desde los repositorios oficiales:
```bash
helm repo add chaos-mesh [https://charts.chaos-mesh.org](https://charts.chaos-mesh.org)
helm install chaos-mesh chaos-mesh/chaos-mesh -n=chaos-mesh --create-namespace --set chaosDaemon.runtime=docker --set chaosDaemon.socketPath=/var/run/docker.sock
```

---

### 5. Enlaces caídos o almacenamiento denegado (S3 Access Denied)
**Error:**
```xml
<Error>
  <Code>AccessDenied</Code>
  <Message>Access Denied</Message>
</Error>
```
**Causa:** Al intentar acceder al archivo de instalación de Chaos Mesh a través del navegador web, el servidor de almacenamiento (Amazon S3) deniega el acceso. Esto sucede porque los mantenedores de la herramienta eliminaron o movieron el archivo YAML estático de esa ruta específica, rompiendo la compatibilidad con instalaciones manuales antiguas.
**Solución:** Desplegar los componentes utilizando la herramienta de gestión **Helm** (detallada en el punto anterior), la cual apunta dinámicamente a los registros actualizados de la aplicación.

---

### 6. Demora prolongada en estado `ContainerCreating`
**Síntoma:** Al ejecutar `kubectl get pods -n chaos-mesh`, los componentes de la arquitectura del caos permanecen varios minutos con el estado `ContainerCreating`.
**Causa:** El motor de Chaos Engineering es robusto e incluye múltiples herramientas (Dashboard, controladores, servidores DNS y Daemons). La primera vez que se instala, Minikube debe descargar varias imágenes pesadas de Docker desde internet hacia el entorno local.
**Solución:** Es un comportamiento normal que depende de la velocidad de la red (suele tardar entre 3 y 5 minutos). Se debe inspeccionar el progreso en tiempo real usando la bandera de observación dinámica:
```bash
kubectl get pods -n chaos-mesh -w
```

---

### 7. Componentes generadores de carga con estado de `Error`
**Síntoma:** Al listar los pods del clúster, los contenedores de estrés viejos (`load-generator`) muestran un estado persistente de `Error`.
**Causa:** Esto ocurre porque los procesos de ataque fueron finalizados de manera forzada por el usuario utilizando señales de interrupción (`Ctrl + C`). Kubernetes registra que el proceso dentro del contenedor no terminó con un código de salida exitoso (código 0) y lo marca como fallido. Estos pods están completamente inactivos y no consumen recursos de CPU ni memoria.
**Solución:** Son remanentes inofensivos. Si se desea limpiar el panel visual de la terminal, se pueden eliminar manualmente con el comando:
```bash
kubectl delete pod <nombre-del-pod-en-error>
```

---

### 8. Archivo de manifiesto no encontrado
**Síntoma:** Mensaje de error indicando que el archivo de configuración no existe al intentar desplegar un recurso.
**Causa:** Intentar aplicar una configuración (como el ataque a la base de datos) antes de haber creado físicamente el archivo declarativo dentro del directorio del proyecto, o debido a una discrepancia en el nombre del archivo.
**Solución:** Asegurarse de estructurar y guardar el archivo YAML con el nombre exacto antes de invocar la API de Kubernetes.

---

### 9. Error de validación estricta en la API del Caos
**Error:**
```text
strict decoding error: unknown field "spec.scheduler"
```
**Causa:** Las versiones de la API de Chaos Mesh (`chaos-mesh.org/v1alpha1`) implementadas a través de Helm actualizaron sus esquemas de validación (*CRDs*). El campo `scheduler` fue deprecado y removido de la especificación directa del recurso `PodChaos`, requiriendo flujos de agenda externos para ejecuciones cíclicas.
**Solución:** Remover el bloque de temporización (`scheduler`) del archivo declarativo para transformar el experimento en un ataque de tipo "francotirador" (un solo disparo inmediato), permitiendo que la API procese el archivo de forma nativa.

*Manifiesto `k8s/redis-chaos.yaml` Corregido:*
```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: matar-redis
  namespace: default
spec:
  action: pod-kill
  mode: one 
  selector:
    labelSelectors:
      app: redis
```