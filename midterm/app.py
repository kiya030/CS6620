#!/usr/bin/env python3

import aws_cdk as cdk
from stacks.storage_replicator_stack import StorageReplicatorStack
from stacks.cleaner_stack import CleanerStack

app = cdk.App()

# Deploy the combined Storage + Replicator stack
storage_replicator_stack = StorageReplicatorStack(app, "StorageReplicatorStack")

# Deploy CleanerStack (only depends on the merged stack)
cleaner_stack = CleanerStack(app, "CleanerStack", storage=storage_replicator_stack)

app.synth()
