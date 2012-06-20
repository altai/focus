Feature: Projects Management for Global Admin

  Scenario: Network Label Gets Changed During Project Lifecycle
    Given I am logged in as admin "admin"
    And I created network with vlan "foo"
    When I visit networks
    Then I see network with vlan "foo" and label "netfoo"
    When I create project with name "bar" and network with label "netfoo"
    And I visit networks
    Then I see network with vlan "foo" and label "bar"
    When I delete project with name "bar"
    And I visit networks
    Then I see network with vlan "foo" and label "netfoo"
