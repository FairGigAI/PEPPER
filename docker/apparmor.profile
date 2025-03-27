# TODO: Complete AppArmor profile implementation
# This file will contain the AppArmor profile for container security
# Current status: In progress - needs to be completed with proper security rules
# Last updated: March 25, 2024

# AppArmor profile for P.E.P.P.E.R. agents
# Last updated: March 26, 2024

profile agent {
  #include <abstractions/base>
  #include <abstractions/python>
  #include <abstractions/openssl>
  #include <abstractions/ssl_keys>
  
  # Python-specific paths
  /usr/local/lib/python3.11/** r,
  /usr/local/bin/python3.11 r,
  /usr/local/bin/pip3 r,
  
  # Application paths
  /app/** rw,  # Main application directory
  /app/logs/** rw,  # Log files
  /app/output/** rw,  # Output files
  /app/config/** r,  # Configuration files (read-only)
  
  # Temporary files
  /tmp/** rw,
  
  # Git operations
  /usr/bin/git r,
  /usr/bin/git-* r,
  
  # Network access
  network inet tcp,  # IPv4 TCP
  network inet udp,  # IPv4 UDP
  network inet6 tcp, # IPv6 TCP
  network inet6 udp, # IPv6 UDP
  
  # Process execution
  deny /proc/** w,  # Prevent writing to procfs
  deny /sys/** w,   # Prevent writing to sysfs
  /proc/sys/** r,   # Allow reading system info
  /proc/cpuinfo r,
  /proc/meminfo r,
  
  # Resource limits
  deny /dev/mem w,    # Prevent direct memory access
  deny /dev/kmem w,   # Prevent kernel memory access
  deny /dev/port w,   # Prevent I/O port access
  /dev/urandom r,     # Allow reading random numbers
  /dev/random r,      # Allow reading random numbers
  
  # Mount points
  deny mount,         # Prevent mounting new filesystems
  deny remount,       # Prevent remounting filesystems
  deny pivot_root,    # Prevent changing root directory
  
  # Capabilities
  deny capability sys_admin,    # Prevent system administration
  deny capability sys_module,   # Prevent loading kernel modules
  deny capability sys_resource, # Prevent resource control
  deny capability sys_time,     # Prevent time manipulation
  
  # Additional security measures
  deny /var/log/** w,  # Prevent writing to system logs
  deny /var/run/** w,  # Prevent writing to runtime data
  deny /var/cache/** w, # Prevent writing to cache
  deny /var/tmp/** w,   # Prevent writing to temp files
  
  # Allow necessary system calls
  deny sysctl,         # Prevent system control
  deny syslog,         # Prevent system logging
  deny setuid,         # Prevent privilege escalation
  deny setgid,         # Prevent group privilege changes
  
  # Python package management
  /usr/local/lib/python3.11/site-packages/** r,
  /usr/local/lib/python3.11/dist-packages/** r,
  
  # Development tools
  /usr/bin/curl r,
  /usr/bin/wget r,
  
  # File operations
  deny /etc/** w,  # Prevent writing to system configs
  deny /var/** w,  # Prevent writing to system data
  deny /usr/** w,  # Prevent writing to system binaries
  deny /bin/** w,  # Prevent writing to system binaries
  deny /sbin/** w, # Prevent writing to system binaries
  
  # Allow read-only access to necessary system files
  /etc/hosts r,
  /etc/resolv.conf r,
  /etc/localtime r,
  /etc/timezone r,
  
  # Memory management
  deny /dev/shm/** w,  # Prevent shared memory access
  deny /dev/mqueue/** w,  # Prevent message queue access
  
  # IPC
  deny /dev/socket/** w,  # Prevent socket access
  deny /dev/pipe/** w,    # Prevent pipe access
} 