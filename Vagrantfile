Vagrant.configure("2") do |config|
  
  config.vm.box = "ubuntu/trusty64"
  
  config.vm.provision "shell", inline: "mkdir -p /app"
  
  config.vm.synced_folder ".", "/app/repo"
  
  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--memory", "1024"]
  end
  
  config.vm.provision "shell", path: "provision.sh"
  
  config.vm.network "private_network", ip: "192.168.2.100"
  config.vm.network "forwarded_port", guest: 80, host: 8080
  
end