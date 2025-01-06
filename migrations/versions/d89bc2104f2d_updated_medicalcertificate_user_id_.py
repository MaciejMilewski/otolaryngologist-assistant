"""Updated MedicalCertificate user_id nullable false

Revision ID: d89bc2104f2d
Revises: 794485435350
Create Date: 2025-01-06 12:11:16.101489

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd89bc2104f2d'
down_revision = '794485435350'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('medical_certificate', schema=None) as batch_op:
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=False)

    with op.batch_alter_table('visit', schema=None) as batch_op:
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('patient_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.create_index(batch_op.f('ix_visit_user_id'), ['user_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('visit', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_visit_user_id'))
        batch_op.alter_column('patient_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    with op.batch_alter_table('medical_certificate', schema=None) as batch_op:
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    # ### end Alembic commands ###
