"""Updated MedicalCertificate added location

Revision ID: 26dc6ce54448
Revises: 55efa92bbbdb
Create Date: 2024-12-30 18:06:01.653975

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '26dc6ce54448'
down_revision = '55efa92bbbdb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('medical_certificate', schema=None) as batch_op:
        batch_op.add_column(sa.Column('location', sa.String(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('medical_certificate', schema=None) as batch_op:
        batch_op.drop_column('location')

    # ### end Alembic commands ###
