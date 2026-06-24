# Lightweight Dockerfile that uses the official Kivy/Buildozer image
# This image is suitable for local builds. It does not run the build during image creation.
FROM kivy/buildozer:latest

WORKDIR /home/user/project

# Copy project files into image (useful for building inside container)
COPY . /home/user/project

# Provide a non-root user option if necessary (image already configures user)
USER root

# Default command prints a hint; use docker run to execute buildozer commands
CMD ["/bin/bash"]
