pipeline {
    agent any

    triggers {
        githubPush()
    }

    stages {
        stage('Install/Update Packages') {
            steps {
                sh '''
                pip3 install ncclient pandas ipaddress netaddr prettytable pylint pytest --upgrade
                '''
            }
        }

        stage('Check PEP8 Style with Pylint') {
            steps {
                sh '''
                   python3 -m pylint --fail-under=5 netman_netconf_obj2.py
                '''
            }
        }

        stage('Run Application') {
            steps {
                sh '''
                    python3 netman_netconf_obj2.py
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    python3 -m pytest test_netconf.py -v
                '''
            }
        }
    }

    post {
        success {
            mail to: 'dheerajgajula.cse@gmail.com',
                 subject: "Jenkins Build SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                 body: "Build ${env.BUILD_URL} completed successfully. "
        }
        failure {
            mail to: 'dheerajgajula.cse@gmail.com',
                 subject: "Jenkins Build FAILURE: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                 body: "Build ${env.BUILD_URL} failed. Please check the console output."
        }
    }
}